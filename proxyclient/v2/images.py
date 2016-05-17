"""
images interface
"""
from six.moves.urllib import parse

from proxyclient import base

class Image(base.Resource):
    def __repr__(self):
        return "<Image: %s>" % self.name

class ImageManager(base.Manager):
    resource_class = Image

    def get(self, zone, filters=None):
        query_string = "?%s" % parse.urlencode(filters) if filters else ""
        return self._list('/images/%s%s' % (base.getid(zone), query_string),
                          'images')

    def list(self):
        return self._list('/images', 'images')

    def delete(self, image_id):
        return self._delete('/images/%s' % image_id)

    def rebuild(self, zone):
        body = {'zone_id': base.getid(zone)}
        return self._update('/images', body)
