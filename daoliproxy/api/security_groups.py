import collections
import webob
from webob import exc

from oslo_config import cfg
from oslo_log import log as logging

from daoliproxy.api.base import BaseController
from daoliproxy.api.openstack import wsgi
from daoliproxy import exception
from daoliproxy.i18n import _

from proxyclient.client import HTTPClient


controller_opt = cfg.StrOpt('controller_url',
                            default='http://127.0.0.1:8081',
                            help='The openflow controller url')

CONF = cfg.CONF
CONF.register_opt(controller_opt)

LOG = logging.getLogger(__name__)

class Controller(BaseController):
    """The zone API controller.
    """
    def __init__(self, **kwargs):
        self.client = HTTPClient(http_log_debug=CONF.debug)
        self.client.set_management_url(CONF.controller_url)
        super(BaseController, self).__init__(**kwargs)

    def list(self, req):
        context = req.environ['proxy.context']
        security_groups = collections.defaultdict(set)

        for group in self.db.security_group_get(
                context, context.user_id):
            security_groups[group.start].add(group.end)
            security_groups[group.end].add(group.start)

        return {"security_groups": security_groups}

    def update(self, req, body):
        security_group = self._from_body(body, 'security_group')
        context = req.environ['proxy.context']

        if security_group['action'] == 'create':
            self.db.security_group_create(context,
                                          context.user_id,
                                          security_group['start'],
                                          security_group['end'])
        elif security_group['action'] == 'delete':
            try:
                self.client.put('/v1.0/group', body={
                    'sid': security_group['start'], 'did': security_group['end']})
            except IOError as e:
                LOG.error(e.message)

            self.db.security_group_delete(context,
                                          context.user_id,
                                          security_group['start'],
                                          security_group['end'])
        return webob.Response(status_int=202)

def create_resource():
    return wsgi.Resource(Controller())
