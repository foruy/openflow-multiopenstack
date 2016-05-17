"""
gateways interface
"""

from proxyclient import base

class Gateway(base.Resource):
    def __repr__(self):
        return "<Gateway: %s>" % self.name

class GatewayManager(base.Manager):
    resource_class = Gateway

    def get_by_instance(self, instance_id):
        return self._list('/os-gateways/instance/%s' % instance_id, 'gateways')

    def get_by_zone(self, zone):
        return self._list('/os-gateways/zone/%s' % base.getid(zone), 'gateways')

    def list(self):
        return self._list('/gateways', 'gateways')

    def delete(self, gateway_id):
        return self._delete('/gateway/%s' % gateway_id)

    def rebuild(self, zone):
        body = {'zone_id': base.getid(zone)}
        return self._update('/gateways', body)
