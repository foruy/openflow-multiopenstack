import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from keystoneclient import exceptions as keystone_exceptions
from openstack_dashboard.exceptions import KeystoneAuthException

from . import user as auth_user
from openstack_dashboard.utils import get_keystone_client
from openstack_dashboard.utils import get_client_addr
from openstack_dashboard.utils import get_client_type

from openstack_dashboard.api.proxy import proxy_client

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
            token = self.request.session['token']
            user = auth_user.create_user_from_token(self.request, token)
            return user
        else:
            return None

    def authenticate(self, request=None, username=None,
                     password=None, auth_url=None):
        """Authenticates a user via the Keystone Identity API. """
        LOG.debug('Beginning user authentication for user "%s".' % username)

        try:
            client = proxy_client.Client(username, password,
                                         auth_token=settings.AUTH_TOKEN,
                                         bypass_url=settings.MANAGEMENT_URL,
                                         insecure=False, cacert=None,
                                         http_log_debug=settings.DEBUG)

            auth_ref = client.users.authenticate(username, password,
                                                 user_addr=get_client_addr(request),
                                                 user_type=get_client_type(request))
        except:
            msg = _("Invalid user name or password.")
            raise KeystoneAuthException(msg)

        # If we made it here we succeeded. Create our User!
        user = auth_user.create_user_from_token(request, auth_user.Token(auth_ref))

        if request is not None:
            request.user = user

        LOG.debug('Authentication completed for user "%s".' % username)
        return user

    def get_group_permissions(self, user, obj=None):
        """Returns an empty set since Keystone doesn't support "groups"."""
        return set()

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

    def has_module_perms(self, user, app_label):
        """Returns True if user has any permissions in the given app_label.

        Currently this matches for the app_label ``"openstack"``.
        """
        if not user.is_active:
            return False
        for perm in self.get_all_permissions(user):
            if perm[:perm.index('.')] == app_label:
                return True
        return False
