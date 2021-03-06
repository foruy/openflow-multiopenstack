# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import hashlib
import logging

#from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from django.contrib.auth import models
from django.db import models as dbmodels

#from keystoneclient import exceptions as keystone_exceptions

from openstack_dashboard.utils import check_token_expiration
#from .utils import get_keystone_version
#from .utils import get_project_list
#from .utils import is_ans1_token


LOG = logging.getLogger(__name__)


def set_session_from_user(request, user):
    request.session['token'] = user.token
    request.session['user_id'] = user.id
    request.session['status'] = True
    # Update the user object cached in the request
    request._cached_user = user
    request.user = user

def create_user_from_token(request, token):
    return User(id=token.user['id'],
                token=token,
                user=token.user['name'],
                project_id=token.project['id'],
                project_name=token.project['name'],
                enabled=True)

class Token(object):
    """Token object that encapsulates the auth_ref (AccessInfo)from keystone
       client.

       Added for maintaining backward compatibility with horizon that expects
       Token object in the user object.
    """
    def __init__(self, auth_ref):
        # User-related attributes
        user = {}
        user['id'] = auth_ref.id
        user['name'] = auth_ref.username
        self.user = user

        #Token-related attributes
        self.id = auth_ref.auth_token
        if len(self.id) > 64:
            algorithm = getattr(settings, 'OPENSTACK_TOKEN_HASH_ALGORITHM',
                                'MD5')
            hasher = hashlib.new(algorithm)
            hasher.update(self.id)
            self.id = hasher.hexdigest()
        self.expires = auth_ref.expires

        # Project-related attributes
        project = {}
        project['id'] = auth_ref.project_id
        project['name'] = auth_ref.username
        self.project = project
        self.tenant = self.project

class User(models.AbstractBaseUser, models.PermissionsMixin):
    """A User class with some extra special sauce for Keystone.

    In addition to the standard Django user attributes, this class also has
    the following:

    .. attribute:: token

        The Keystone token object associated with the current user/tenant.

        The token object is deprecated, user auth_ref instead.

    .. attribute:: tenant_id

        The id of the Keystone tenant for the current user/token.

        The tenant_id keyword argument is deprecated, use project_id instead.

    .. attribute:: tenant_name

        The name of the Keystone tenant for the current user/token.

        The tenant_name keyword argument is deprecated, use project_name
        instead.

    .. attribute:: project_id

        The id of the Keystone project for the current user/token.

    .. attribute:: project_name

        The name of the Keystone project for the current user/token.

    .. attribute:: service_catalog

        The ``ServiceCatalog`` data returned by Keystone.

    .. attribute:: roles

        A list of dictionaries containing role names and ids as returned
        by Keystone.

    .. attribute:: services_region

        A list of non-identity service endpoint regions extracted from the
        service catalog.

    .. attribute:: user_domain_id

        The domain id of the current user.

    .. attribute:: domain_id

        The id of the Keystone domain scoped for the current user/token.

    """

    USERNAME_FIELD = 'id'
    id = dbmodels.CharField(max_length=240, primary_key=True)

    def __init__(self, id=None, token=None, user=None, roles=None,
                 enabled=False, project_id=None, project_name=None,
                 password=None):
        self.id = id
        self.pk = id
        self.token = token
        self.username = user
        self.project_id = project_id
        self.project_name = project_name
        #self.roles = roles or []
        self.roles = [{'name': ('admin'
            if 'admin' == self.username else 'member')}]
        self.enabled = enabled

        self.password = None
        self.USERNAME_FIELD = self.username

    def __unicode__(self):
        return self.username

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.username)

    def is_token_expired(self):
        """
        Returns ``True`` if the token is expired, ``False`` if not, and
        ``None`` if there is no token set.
        """
        if self.token is None:
            return None
        return not check_token_expiration(self.token)

    def is_authenticated(self):
        """ Checks for a valid token that has not yet expired. """
        #return self.token is not None and check_token_expiration(self.token)
        return self.id is not None and self.token is not None

    def is_anonymous(self):
        """
        Returns ``True`` if the user is not authenticated,``False`` otherwise.
        """
        return not self.is_authenticated()

    @property
    def is_active(self):
        return self.enabled

    @property
    def is_superuser(self):
        """
        Evaluates whether this user has admin privileges. Returns
        ``True`` or ``False``.
        """
        return 'admin' in [role['name'].lower() for role in self.roles]

    #@property
    #def authorized_tenants(self):
    #    """ Returns a memoized list of tenants this user may access. """
    #    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    #    ca_cert = getattr(settings, "OPENSTACK_SSL_CACERT", None)

    #    if self.is_authenticated() and self._authorized_tenants is None:
    #        endpoint = self.endpoint
    #        token = self.token
    #        try:
    #            self._authorized_tenants = get_project_list(
    #                user_id=self.id,
    #                auth_url=endpoint,
    #                token=token.id,
    #                insecure=insecure,
    #                cacert=ca_cert,
    #                debug=settings.DEBUG)
    #        except (keystone_exceptions.ClientException,
    #                keystone_exceptions.AuthorizationFailure):
    #            LOG.exception('Unable to retrieve project list.')
    #    return self._authorized_tenants or []

    #@authorized_tenants.setter
    #def authorized_tenants(self, tenant_list):
    #    self._authorized_tenants = tenant_list

    def default_services_region(self):
        """
        Returns the first endpoint region for first non-identity service
        in the service catalog
        """
        if self.service_catalog:
            for service in self.service_catalog:
                if service['type'] == 'identity':
                    continue
                for endpoint in service['endpoints']:
                    return endpoint['region']
        return None

    @property
    def services_region(self):
        return self._services_region

    @services_region.setter
    def services_region(self, region):
        self._services_region = region

    @property
    def available_services_regions(self):
        """
        Returns list of unique region name values found in service catalog
        """
        regions = []
        if self.service_catalog:
            for service in self.service_catalog:
                if service['type'] == 'identity':
                    continue
                for endpoint in service['endpoints']:
                    if endpoint['region'] not in regions:
                        regions.append(endpoint['region'])
        return regions

    def save(*args, **kwargs):
        # Presume we can't write to Keystone.
        pass

    def delete(*args, **kwargs):
        # Presume we can't write to Keystone.
        pass

    # Check for OR'd permission rules, check that user has one of the
    # required permission.
    def has_a_matching_perm(self, perm_list, obj=None):
        """
        Returns True if the user has one of the specified permissions. If
        object is passed, it checks if the user has any of the required perms
        for this object.
        """
        # If there are no permissions to check, just return true
        if not perm_list:
            return True
        # Check that user has at least one of the required permissions.
        for perm in perm_list:
            if self.has_perm(perm, obj):
                return True
        return False

    # Override the default has_perms method. Allowing for more
    # complex combinations of permissions.  Will check for logical AND of
    # all top level permissions.  Will use logical OR for all first level
    # tuples (check that use has one permissions in the tuple)
    #
    # Examples:
    #   Checks for all required permissions
    #   ('openstack.roles.admin', 'openstack.roles.L3-support')
    #
    #   Checks for admin AND (L2 or L3)
    #   ('openstack.roles.admin', ('openstack.roles.L3-support',
    #                              'openstack.roles.L2-support'),)
    def has_perms(self, perm_list, obj=None):
        """
        Returns True if the user has all of the specified permissions.
        Tuples in the list will possess the required permissions if
        the user has a permissions matching one of the elements of
        that tuple
        """
        # If there are no permissions to check, just return true
        if not perm_list:
            return True
        for perm in perm_list:
            if isinstance(perm, basestring):
                # check that the permission matches
                if not self.has_perm(perm, obj):
                    return False
            else:
                # check that a permission in the tuple matches
                if not self.has_a_matching_perm(perm, obj):
                    return False
        return True
