"""
networks interface
"""

from proxyclient import base

class Network(base.Resource):
    def __repr__(self):
        return "<Network: %s>" % self.name

class NetworkManager(base.Manager):
    resource_class = Network

    def get(self, zone):
        return self._list('/networks/%s' % base.getid(zone), 'networks')

    def list(self):
        return self._list('/networks', 'networks')

    def delete(self, network_id):
        return self._delete('/networks/%s' % network_id)

    def rebuild(self, zone):
        body = {'zone_id': base.getid(zone)}
        return self._update('/networks', body)

    def network_type_list(self):
        return self._list('/os-network', 'networks')

    def network_type_delete(self, id):
        self._delete('/os-network/%s' % id)
