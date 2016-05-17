import collections
import webob
from webob import exc

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import timeutils

from daoliproxy import agent
from daoliproxy.api.base import BaseController
from daoliproxy.api.openstack import wsgi
from daoliproxy import exception
from daoliproxy.i18n import _

CONF = cfg.CONF

LOG = logging.getLogger(__name__)

class Controller(BaseController):
    """The resources API controller.
    """
    def list(self, req):
        context = req.environ['proxy.context']
        user_id = req.GET.get('user_id', None)

        if not user_id:
            user_id = context.user_id

        sources = collections.defaultdict(dict)

        for res in self.db.resource_get(context, user_id=user_id):
            if not sources[res.source_id].has_key(res.source_name):
                sources[res.source_id][res.source_name] = []
            sources[res.source_id][res.source_name].append(res)

        resources = []
        for sid, src in sources.items():
            for s in ('instance', 'disk'):
                if src.has_key(s):
                    r = self._format_resource(src[s])
                    if r: resources.append(r)

        return {'resources': resources}

    def get(self, req, user_id):
        context = req.environ['proxy.context']
        source_id = req.GET.get('source_id', None)
        source_name= req.GET.get('source_name', None)

        resources = self.db.resource_get(context,
                                         user_id=user_id,
                                         source_id=source_id,
                                         source_name=source_name)
        return {'resources': resources}

    def consume(self, start, end):
        start_time = start.created_at
        delete_time = None
        if end is None:
            if start.action == 'delete':
                end_time = start.created_at
                delete_time = end_time
            else:
                end_time = timeutils.utcnow()
        else:
            end_time = end.created_at
            if end.action == 'delete':
                delete_time = end_time
        return (start_time, end_time, delete_time)

    def _format_resource(self, source):
        src = dict(source[0], usage=0, deleted_at=timeutils.utcnow())
        if src['action'] == 'create':
            if len(source) % 2 != 0:
                source.append(None)
            for i in xrange(0, len(source), 2):
                start_time, end_time, delete_time = self.consume(
                    source[i], source[i+1])
                src['usage'] += timeutils.delta_seconds(start_time, end_time)
                if delete_time is not None:
                    src['deleted_at'] = delete_time
            return src

def create_resource():
    return wsgi.Resource(Controller())
