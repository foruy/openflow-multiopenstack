import os
import webob
from webob import exc

from oslo_config import cfg
from oslo_log import log as logging

from daoliproxy import agent
from daoliproxy.api.base import BaseController
from daoliproxy.api.openstack import wsgi
from daoliproxy import exception
from daoliproxy.i18n import _
from daoliproxy.linux.network import Network
from daoliproxy import utils

from proxyclient.client import HTTPClient

CONF = cfg.CONF
CONF.import_opt('agent_port', 'daoliproxy.manager')
CONF.import_opt('host', 'daoliproxy.netconf')
CONF.import_opt('my_ip', 'daoliproxy.netconf')
CONF.register_opt(cfg.StrOpt('topic', default='webproxy'))

LOG = logging.getLogger(__name__)

class Controller(BaseController):
    """The gateway API controller.
    """
    def __init__(self, **kwargs):
        self.client = HTTPClient(http_log_debug=CONF.debug)
        super(BaseController, self).__init__(**kwargs)

    def get_by_instance(self, req, instance_id):
        context = req.environ['proxy.context']

        server = self.db.server_get(context, instance_id)
        gateway = self.db.gateway_get(context, server.host)

        if not gateway:
            gateways = []
        else:
            gateways = self.db.gateway_get_by_idc(context, gateway.idc_id)

        return {'gateways': gateways}

    def get_by_zone(self, req, zone_id):
        context = req.environ['proxy.context']
        return {'gateways': self.db.gateway_get_all(context, zone_id)}

    def list(self, req):
        context = req.environ['proxy.context']
        return {'gateways': self.db.gateway_get_all(context)}

    @wsgi.response(204)
    def delete(self, req, gateway_id):
        context = req.environ['proxy.context']
        self.db.gateway_delete(context, gateway_id)

    def _format_gateway(self, gateway):
        _gateway = {}
        return _gateway

    def _rebuild(self, req, body, checked=False):
        zone_id = self._from_body(body, 'zone_id')
        context = req.environ['proxy.context']
        zone = self.db.zone_get(context, zone_id)

        if checked:
            if zone.idc_id != CONF.idc_id:
                return self.proxy_method('gateway_rebuild_proxy',
                        context, zone.idc_id, body)

        self.db.gateway_delete(context, zone_id=zone_id)

        self.client.set_management_url(utils.replace_url(
                zone['auth_url'], port=CONF.agent_port, path=''))
        resp, body = self.client.get('/gateways')

        for gateway in body['gateways']:
            gateway['idc_id'] = CONF.idc_id
            self.db.gateway_create(context, zone_id, gateway)
                
        return webob.Response(status_int=202)

    def _format_service(self):
        _service = {}
        _service['name'] = CONF.host
        _service['url'] = 'http://%s:%s' % (os.environ.get('host',
                CONF.my_ip), CONF.daoliproxy_listen_port)
        _service['topic'] = CONF.topic
        _service['idc_id'] = CONF.idc_id
        return _service

    def service_create(self, req, body):
        context = req.environ['proxy.context']

        if body and body.get('gateway'):
            gateway = body['gateway']
        else:
            gateway = Network.gateway_get()

        if not gateway.has_key('idc_id'):
            gateway['idc_id'] = CONF.idc_id

        service = self.db.service_create(context, self._format_service())
        gateway['zone_id'] = service.id

        host = os.environ.get('host')
        if host:
            gateway['vext_ip'] = host

        if not self.db.gateway_get(context, CONF.host):
            gateway['hostname'] = CONF.host
            self.db.gateway_create(context, service.id, gateway)
        else:
            self.db.gateway_update(context, CONF.host, gateway)

        return {'service': service}

def create_resource():
    return wsgi.Resource(Controller())
