from keystoneclient import exceptions as keystoneclient
from novaclient import exceptions as novaclient
from proxyclient import exceptions as proxyclient

class KeystoneAuthException(Exception):
    """ Generic error class to identify and catch our own errors. """
    pass


UNAUTHORIZED = (
    keystoneclient.Unauthorized,
    keystoneclient.Forbidden,
    novaclient.Unauthorized,
    novaclient.Forbidden,
)

NOT_FOUND = (
    keystoneclient.NotFound,
    novaclient.NotFound,
)

RECOVERABLE = (
    keystoneclient.ClientException,
    # AuthorizationFailure is raised when Keystone is "unavailable".
    keystoneclient.AuthorizationFailure,
    novaclient.ClientException,
)

Unauthorized = proxyclient.Unauthorized
