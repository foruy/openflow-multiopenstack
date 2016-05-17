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
    """The image API controller.
    """
    def get(self, req, zone_id):
        context = req.environ['proxy.context']
        return {'images': self.db.image_get_all(context, zone_id)}

    def list(self, req):
        context = req.environ['proxy.context']
        return {'images': self.db.image_get_all(context)}

    @wsgi.response(204)
    def delete(self, req, image_id):
        context = req.environ['proxy.context']
        self.db.image_delete(context, image_id)

    def _format_image(self, image):
        _image = {}
        _image['imageid'] = image.id
        _image['name'] = image.name
        _image['checksum'] = image.checksum
        _image['container_format'] = image.container_format
        _image['disk_format'] = getattr(image, 'disk_format', 'raw')
        _image['is_public'] = image.is_public
        _image['min_disk'] = image.min_disk
        _image['min_ram'] = image.min_disk
        _image['size'] = image.size
        _image['owner'] = image.owner
        _image['status'] = image.status
        _image['property'] = [22]
        if _image['container_format'] == 'docker':
            try:
                display_format = image.name.split('-')[1].replace('.', '')
            except IndexError:
                display_format = None

            if display_format == 'wordpress':
                _image['property'].append(80)

            _image['display_format'] = display_format
        else:
            _image['display_format'] = 'vm'

        return _image

    def _rebuild(self, req, body, checked=False):
        zone_id = self._from_body(body, 'zone_id')
        context = req.environ['proxy.context']

        if checked:
            zone = self.db.zone_get(context, zone_id)
            if zone.idc_id != CONF.idc_id:
                return self.proxy_method('image_rebuild_proxy', context, body)

        self.db.image_delete(context, zone_id=zone_id)

        images, has_more = agent.image_list_detailed(
                self.request_get(context, zone_id))

        for image in images:
            self.db.image_create(context, zone_id, self._format_image(image))
                
        return webob.Response(status_int=202)

def create_resource():
    return wsgi.Resource(Controller())
