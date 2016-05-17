import webob
from webob import exc

from oslo_config import cfg
from oslo_log import log as logging

from daoliproxy import agent
from daoliproxy.api.base import BaseController
from daoliproxy.api.openstack import wsgi
from daoliproxy import exception
from daoliproxy.i18n import _

CONF = cfg.CONF

LOG = logging.getLogger(__name__)

class Controller(BaseController):
    """The network API controller.
    """
    def get(self, req, zone_id):
        context = req.environ['proxy.context']
        return {'networks': self.db.network_get_all(context, zone_id)}

    def list(self, req):
        context = req.environ['proxy.context']
        return {'networks': self.db.network_get_all(context)}

    @wsgi.response(204)
    def delete(self, req, network_id):
        context = req.environ['proxy.context']
        self.db.network_delete(context, network_id)

    def network_type_list(self, req):
        context = req.environ['proxy.context']
        return {'networks': self.db.network_type_list(context)}

    @wsgi.response(204)
    def network_type_delete(self, req, id):
        context = req.environ['proxy.context']
        self.db.network_type_delete(id)

    def _format_network(self, context, network):
        _network = {}
        _network['networkid'] = network.id
        _network['gateway'] = network.gateway

        netype = self.db.network_type_update(context, network.cidr)

        _network['netype'] = netype.id
        return _network

    def _rebuild(self, req, body, checked=False):
        zone_id = self._from_body(body, 'zone_id')
        context = req.environ['proxy.context']

        if checked:
            zone = self.db.zone_get(context, zone_id)
            if zone.idc_id != CONF.idc_id:
                return self.proxy_method('network_rebuild_proxy', context, body)

        self.db.network_delete(context, zone_id=zone_id)

        networks = agent.network_list(self.request_get(context, zone_id))

        for network in networks:
            self.db.network_create(context, zone_id,
                    self._format_network(context, network))
                
        return webob.Response(status_int=202)

def create_resource():
    return wsgi.Resource(Controller())
