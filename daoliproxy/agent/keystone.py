from oslo.config import cfg
from oslo_log import log as logging

from daoliproxy.api.token import get_keystone_client

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

CACHE_ATTR = {}

def keystoneclient(request, admin=False):
    """Returns a client connected to the Keystone backend."""
    if not CACHE_ATTR.has_key(request.id):
        LOG.debug('novaclient connection created using token "%s" and url "%s"',
                request.auth_token, request.auth_url)
        conn = get_keystone_client().Client(token=request.auth_token,
                                            endpoint=request.auth_url,
                                            auth_url=request.auth_url,
                                            debug=CONF.debug,
                                            timeout=CONF.timeout)
        CACHE_ATTR[request.id] = conn
    return CACHE_ATTR[request.id]

def user_list(request, project=None, domain=None, group=None, filters=None):
    if CONF.identity_version < 3:
        kwargs = {"tenant_id": project}
    else:
        kwargs = {
            "project": project,
            "domain": domain,
            "group": group
        }
        if filters is not None:
            kwargs.update(filters)
    users = keystoneclient(request, admin=True).users.list(**kwargs)
    return users

def tenant_create(request, name=None, description=None,
                  enabled=None, domain=None, **kwargs):
    return keystoneclient(request, admin=True).tenants.create(
        name, description, enabled, **kwargs)

def user_create(request, name=None, email=None, password=None, project=None,
                enabled=None, domain=None):
    manager = keystoneclient(request, admin=True).users
    return manager.create(name, password, email,
        project, enabled)

def user_update_password(request, user, password, admin=True):
    manager = keystoneclient(request, admin=admin).users
    return manager.update_password(user, password)

def tenant_delete(request, project):
    return keystoneclient(request, admin=True).tenants.delete(project)

def user_delete(request, user_id):
    return keystoneclient(request, admin=True).users.delete(user_id)
