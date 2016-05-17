import webob
from webob import exc

from oslo_config import cfg
from oslo_log import log as logging

from daoliproxy import agent
from daoliproxy.api.base import BaseController
from daoliproxy.api.openstack import wsgi
from daoliproxy import exception
from daoliproxy.i18n import _

flavor_opts = [
    cfg.IntOpt('flavor_count', default=2,
               help='Default flavor number for zone'),
]

CONF = cfg.CONF
CONF.register_opts(flavor_opts)

LOG = logging.getLogger(__name__)

class Controller(BaseController):
    """The flavor API controller.
    """
    def get(self, req, zone_id):
        context = req.environ['proxy.context']
        return {'flavors': self.db.flavor_get_all(context, zone_id)}

    def list(self, req):
        context = req.environ['proxy.context']
        return {'flavors': self.db.flavor_get_all(context)}

    @wsgi.response(204)
    def delete(self, req, flavor_id):
        context = req.environ['proxy.context']
        self.db.flavor_delete(context, flavor_id)

    def _format_flavor(self, flavor):
        _flavor = {}
        _flavor['flavorid'] = flavor.id
        _flavor['name'] = flavor.name
        _flavor['vcpus'] = flavor.vcpus
        _flavor['ram'] = flavor.ram
        _flavor['disk'] = flavor.disk
        _flavor['swap'] = flavor.swap
        _flavor['ephemeral'] = getattr(flavor,
            'OS-FLV-EXT-DATA:ephemeral', 0)
        _flavor['rxtx_factor'] = flavor.rxtx_factor
        _flavor['is_public'] = getattr(flavor,
            'os-flavor-access:is_public', True)

        return _flavor

    def _rebuild(self, req, body, checked=False):
        zone_id = self._from_body(body, 'zone_id')
        context = req.environ['proxy.context']

        # proxy -> flavor_rebuild_proxy
        if checked:
            zone = self.db.zone_get(context, zone_id)
            if zone.idc_id != CONF.idc_id:
                return self.proxy_method('flavor_rebuild_proxy', context, body)

        self.db.flavor_delete(context, zone_id=zone_id)

        flavors = agent.flavor_list(self.request_get(context, zone_id))
        if len(flavors) > CONF.flavor_count:
            flavors = flavors[:CONF.flavor_count]

        for flavor in flavors:
            self.db.flavor_create(context, zone_id, self._format_flavor(flavor))
                
        return webob.Response(status_int=202)

def create_resource():
    return wsgi.Resource(Controller())
