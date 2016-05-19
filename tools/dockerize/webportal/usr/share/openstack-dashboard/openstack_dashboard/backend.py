import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from keystoneclient import exceptions as keystone_exceptions
from .exceptions import KeystoneAuthException

from .user import Token
from .user import AuthUser
from .utils import get_keystone_client
from .utils import get_client_addr
from .utils import get_client_type

from openstack_dashboard import api

LOG = logging.getLogger(__name__)

class KeystoneBackend(object):
    """Django authentication backend class for use with
      ``django.contrib.auth``.
    """
    def get_user(self, user_id):
        """Returns the current user (if authenticated) based on the user ID
        and session data.

        Note: this required monkey-patching the ``contrib.auth`` middleware
        to make the ``request`` object available to the auth backend class.
        """
        if (hasattr(self, 'request') and
                user_id == self.request.session["user_id"]):
            username = self.request.session['username']
            token = self.request.session['token']
            user = AuthUser(user_id, username, token)
            return user
        else:
            return None

    def authenticate(self, request=None, username=None,
                     password=None, auth_url=None):
        """Authenticates a user via the Keystone Identity API. """
        LOG.debug('Beginning user authentication for user "%s".' % username)

        try:
            auth_user = api.proxy.authenticate(request, username, password,
                                               user_addr=get_client_addr(request),
                                               user_type=get_client_type(request))
        except:
            msg = _("Invalid user name or password.")
            raise KeystoneAuthException(msg)

        user = AuthUser(auth_user.id, auth_user.username, auth_user.id)

        if request is not None:
            request.user = user

        LOG.debug('Authentication completed for user "%s".' % username)
        return user

    def get_all_permissions(self, user, obj=None):
        """Returns a set of permission strings that this user has through
           his/her Keystone "roles".

          The permissions are returned as ``"openstack.{{ role.name }}"``.
        """
        if user.is_anonymous() or obj is not None:
            return set()
        role_perms = set(["openstack.roles.%s" % role['name'].lower()
                          for role in user.roles])
        return role_perms

    def has_perm(self, user, perm, obj=None):
        """Returns True if the given user has the specified permission. """
        if not user.is_active:
            return False
        return perm in self.get_all_permissions(user, obj)
