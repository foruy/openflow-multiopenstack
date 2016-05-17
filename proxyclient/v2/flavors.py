"""
flavors interface
"""

from proxyclient import base

class Flavor(base.Resource):
    def __repr__(self):
        return "<Flavor: %s>" % self.name

class FlavorManager(base.Manager):
    resource_class = Flavor

    def get(self, zone):
        return self._list('/flavors/%s' % base.getid(zone), 'flavors')

    def list(self):
        return self._list('/flavors', 'flavors')

    def delete(self, flavor_id):
        return self._delete('/flavors/%s' % flavor_id)

    def rebuild(self, zone):
        body = {'zone_id': base.getid(zone)}
        return self._update('/flavors', body)
