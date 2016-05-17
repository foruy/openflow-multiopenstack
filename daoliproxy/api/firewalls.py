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
    """The firewall API controller.
    """
    def get(self, req, id):
        context = req.environ['proxy.context']
        firewalls = self.db.firewall_get_by_instance(context, id)
        return {'firewalls': firewalls}

    @wsgi.response(204)
    def delete(self, req, id):
        context = req.environ['proxy.context']
        self.db.firewall_delete(context, id)
        return webob.Response(status_int=202)

    def create(self, req, body):
        firewall = self._from_body(body, 'firewall')
        context = req.environ['proxy.context']
        return self._firewall_create(context, firewall)

    def exists(self, req, instance_id, body):
        firewall = self._from_body(body, 'firewall')
        context = req.environ['proxy.context']

        firewall = self.db.firewall_get(context,
                hostname=firewall['hostname'],
                gateway_port=firewall['gateway_port'])

        if firewall:
            #raise exc.HTTPConflict()
            return webob.Response(status_int=409)
        else:
            return webob.Response(status_int=202)

def create_resource():
    return wsgi.Resource(Controller())
