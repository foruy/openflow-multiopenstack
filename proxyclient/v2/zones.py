"""
zones interface
"""

from proxyclient import base

class Zone(base.Resource):
    def __repr__(self):
        return "<Zone: %s>" % self.name

class ZoneManager(base.Manager):
    resource_class = Zone

    def list(self, detail=False):
        return self._list('/zones?detail=%s' % detail, 'zones')

    def get(self, id):
        return self._get('/zones/%s' % id, 'zone')
