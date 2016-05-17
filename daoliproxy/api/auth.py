"""
Common Auth Middleware.
"""

from oslo_config import cfg
from oslo_log import log as logging
from oslo_middleware import request_id
import webob.dec
import webob.exc

from daoliproxy import context
import daoliproxy.db as db_api
from daoliproxy import exception
from daoliproxy.i18n import _
from daoliproxy import wsgi

auth_opts = [
    cfg.StrOpt('admin_token', secret=True, default='ADMIN',
               help='A "shared secret" that can be used to bootstrap Keystone'),
    cfg.BoolOpt('use_forwarded_for',
                default=False,
                help='Treat X-Forwarded-For as the canonical remote address. '
                     'Only enable this if you have a sanitizing proxy.')
]

CONF = cfg.CONF
CONF.register_opts(auth_opts)


class KeystoneContext(wsgi.Middleware):
    """Make a request context from keystone headers."""

    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        user_id = req.headers.get('X-Auth-User-Id')
        if user_id is None:
            LOG.debug("Neither X_USER_ID nor X_USER found in request")
            return webob.exc.HTTPUnauthorized()

        roles = self._get_roles(req)

        user_name = req.headers.get('X-Auth-User-Name', user_id)
        project_id = req.headers.get('X-Auth-Project-Id')
        req_id = req.environ.get(request_id.ENV_REQUEST_ID)

        auth_token = req.headers.get('X-Auth-Token')

        if not auth_token:
            raise webob.exc.HTTPUnauthorized()

        service_catalog = {}

        if auth_token == CONF.admin_token:
            is_admin = True
        else:
            is_admin = False
            _context = context.get_admin_context()

            try:
                token = db_api.user_token_get(_context, auth_token)
                if user_id != token.user_id:
                    raise exception.TokenNotFound(token=token)
            except exception.TokenNotFound:
                raise webob.exc.HTTPUnauthorized()

            for kt in db_api.keystone_token_get(_context, auth_token):
                service_catalog[kt.zone_id] = {'catalog': kt.catalog,
                                               'token': kt.id}
                                               #'project_id': kt.project_id,
                                               #'user_id': kt.user_id}

        # Build a context, including the auth_token...
        remote_address = req.remote_addr
        if CONF.use_forwarded_for:
            remote_address = req.headers.get('X-Forwarded-For', remote_address)

        ctx = context.RequestContext(user_id,
                                     project_id,
                                     user_name=user_name,
                                     project_name=user_name,
                                     roles=roles,
                                     auth_token=auth_token,
                                     remote_address=remote_address,
                                     service_catalog=service_catalog,
                                     request_id=req_id)

        req.environ['proxy.context'] = ctx
        return self.application

    def _get_roles(self, req):
        """Get the list of roles."""

        if 'X_ROLES' in req.headers:
            roles = req.headers.get('X_ROLES', '')
        else:
            # Fallback to deprecated role header:
            roles = req.headers.get('X_ROLE', '')
            if roles:
                LOG.warn(_LW("Sourcing roles from deprecated X-Role HTTP "
                             "header"))
        return [r.strip() for r in roles.split(',')]
