from oslo_log import log as logging
import routes

from daoliproxy.api.openstack import extensions
from daoliproxy.api.openstack import wsgi
from daoliproxy.i18n import _, _LC, _LE, _LI, _LW
from daoliproxy import wsgi as base_wsgi

LOG = logging.getLogger(__name__)

class APIMapper(routes.Mapper):
    def routematch(self, url=None, environ=None):
        if url == "":
            result = self._match("", environ)
            return result[0], result[1]
        return routes.Mapper.routematch(self, url, environ)

    def connect(self, *args, **kargs):
        # NOTE(vish): Default the format part of a route to only accept json
        #             and xml so it doesn't eat all characters after a '.'
        #             in the url.
        kargs.setdefault('requirements', {})
        if not kargs['requirements'].get('format'):
            kargs['requirements']['format'] = 'json|xml'
        return routes.Mapper.connect(self, *args, **kargs)

class ProjectMapper(APIMapper):
    def resource(self, member_name, collection_name, **kwargs):
        if 'parent_resource' not in kwargs:
            kwargs['path_prefix'] = '{project_id}/'
        else:
            parent_resource = kwargs['parent_resource']
            p_collection = parent_resource['collection_name']
            p_member = parent_resource['member_name']
            kwargs['path_prefix'] = '{project_id}/%s/:%s_id' % (p_collection,
                                                                p_member)
        routes.Mapper.resource(self, member_name,
                                     collection_name,
                                     **kwargs)

class APIRouter(base_wsgi.Router):
    """Routes requests on the OpenStack API to the appropriate controller
    and method.
    """
    ExtensionManager = None  # override in subclasses

    @classmethod
    def factory(cls, global_config, **local_config):
        """Simple paste factory, :class:`nova.wsgi.Router` doesn't have one."""
        return cls()

    def __init__(self, ext_mgr=None, init_only=None):
        if ext_mgr is None:
            if self.ExtensionManager:
                ext_mgr = self.ExtensionManager()
            else:
                raise Exception(_("Must specify an ExtensionManager class"))

        mapper = ProjectMapper()
        self.resources = {}
        self._setup_routes(mapper, ext_mgr, init_only)
        self._setup_ext_routes(mapper, ext_mgr, init_only)
        self._setup_extensions(ext_mgr)
        super(APIRouter, self).__init__(mapper)

    def _setup_ext_routes(self, mapper, ext_mgr, init_only):
        for resource in ext_mgr.get_resources():
            LOG.debug('Extending resource: %s',
                      resource.collection)

            if init_only is not None and resource.collection not in init_only:
                continue
            inherits = None
            if resource.inherits:
                inherits = self.resources.get(resource.inherits)
                if not resource.controller:
                    resource.controller = inherits.controller
            wsgi_resource = wsgi.Resource(resource.controller,
                                          inherits=inherits)
            self.resources[resource.collection] = wsgi_resource
            kargs = dict(
                controller=wsgi_resource,
                collection=resource.collection_actions,
                member=resource.member_actions)

            if resource.parent:
                kargs['parent_resource'] = resource.parent

            mapper.resource(resource.collection, resource.collection, **kargs)

            if resource.custom_routes_fn:
                resource.custom_routes_fn(mapper, wsgi_resource)

    def _setup_extensions(self, ext_mgr):
        for extension in ext_mgr.get_controller_extensions():
            collection = extension.collection
            controller = extension.controller
            msg_format_dict = {'collection': collection,
                               'ext_name': extension.extension.name}
            if collection not in self.resources:
                LOG.warning(_LW('Extension %(ext_name)s: Cannot extend '
                                'resource %(collection)s: No such resource'),
                            msg_format_dict)
                continue

            LOG.debug('Extension %(ext_name)s extended resource: '
                      '%(collection)s',
                      msg_format_dict)

            resource = self.resources[collection]
            resource.register_actions(controller)
            resource.register_extensions(controller)

    def _setup_routes(self, mapper, ext_mgr, init_only):
        raise NotImplementedError()
