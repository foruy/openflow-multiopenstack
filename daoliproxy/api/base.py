import os
from webob import exc
from oslo_config import cfg
from oslo_serialization import jsonutils

from daoliproxy import agent
from daoliproxy.api import token
from daoliproxy.db import base
from daoliproxy.api.openstack import wsgi
from daoliproxy.openstack.common import threadgroup
from daoliproxy import utils

base_opts = [
    cfg.IntOpt('admin_port', default=35357, help='Keystone admin port'),
    cfg.IntOpt('idc_id', default=os.environ.get('idc_id', 0),
               help='The idc identification'),
]

CONF = cfg.CONF
CONF.register_opts(base_opts)
                  

class MixinController(base.Base, wsgi.Controller):
    def __init__(self, **kwargs):
        super(MixinController, self).__init__(**kwargs)
        self.tg = threadgroup.ThreadGroup(kwargs.get('threads', 10000))

    def _from_body(self, body, key):
        if not body:
            raise exc.HTTPUnprocessableEntity()
        value = body.get(key, None)
        if value is None:
            raise exc.HTTPUnprocessableEntity()
        return value

    def add_thread(self, callback, *args, **kwargs):
        self.tg.add_thread(callback, *args, **kwargs)

    def proxy_method(self, callback, context, idc_id, *args, **kwargs):
        services = self.db.service_get_by_idc(context, idc_id)
        if len(services) < 1:
            msg = _("Availiable idc could not be found.")
            raise exc.HTTPNotFound(explanation=msg)

        if not hasattr(agent, callback):
            msg = _("The proxy method %s could be found.")
            raise AttributeError(msg % callback)

        context.auth_url = services[0].url

        return getattr(agent, callback)(context, *args, **kwargs)

    def rebuild(self, req, body):
        return self._rebuild(req, body)

    def rebuild_proxy(self, req, body):
        return self._rebuild(req, body, checked=False)

    def _rebuild(self, req, body, checked=False):
        raise NotImplementedError()

    def request_get(self, context, zone_id):
        service_catalog = context.service_catalog.get(zone_id)

        if not service_catalog:
            raise exc.HTTPUnauthorized()

        context.auth_token = service_catalog['token']
        context.catalog = service_catalog['catalog']

        return context

class BaseController(MixinController):

    def _authenticate(self, context, user, zone):
        token_obj = token.authentication(user.username,
                                         user.password,
                                         zone.auth_url)

        token_ref = self.db.keystone_token_create(
                context, id=token_obj.id, user_id=token_obj.user_id,
                project_id=token_obj.project_id, expires=token_obj.expires,
                user_token_id=context.auth_token, catalog=token_obj.catalog,
                zone_id=zone.id)

        return token_ref

    def _register_thread(self, context, zone, auth, checked=False):
        # proxy -> register_proxy
        if checked and zone.idc_id != CONF.idc_id:
            return self.proxy_method('register_proxy',
                                     context, zone.idc_id,
                                     auth.id, zone.id)

        zone.auth_url = utils.replace_url(zone.auth_url, port=CONF.admin_port)

        def _register_try(func, **kwargs):
            try_count = 1
            while try_count > 0:
                try_count -= 1
                try:
                    return func(zone, **kwargs)
                except Exception as e:
                    excep = e
                    #greenthread.sleep(2)

            if try_count <= 0:
                # Store database on error
                auth['method'] = func.__name__
                auth['message']= excep.message
                auth['auth_url'] = zone.auth_url
                self.db.user_task(context, 'register',
                                  jsonutils.dumps(jsonutils.to_primitive(auth)))
                raise excep

        tenant_obj = _register_try(agent.tenant_create,
                                   name=auth['username'],
                                   description='%s tenant' % auth['username'],
                                   enabled=True)

        user_obj = _register_try(agent.user_create,
                                 name=auth['username'],
                                 email=auth['email'],
                                 password=auth['password'],
                                 project=tenant_obj.id,
                                 enabled=True)

        #self.db.user_project_create(auth.id, tenant_obj.id, user_obj.id,
        #                            request.id, request.default_instances)
        #LOG.debug('User "%s" on "%s" register successful' % (
        #    auth['username'], zone.auth_url))

    def _firewall_create(self, context, firewall):
        server = self.db.server_get(context, firewall['instance_id'])
        firewall_zone = self.db.gateway_get(context, firewall['hostname'])
        firewall['fake_zone'] = (server['zone_id'] == firewall_zone['zone_id'])
        self.db.firewall_create(context, firewall)
        return {'firewall': firewall}
