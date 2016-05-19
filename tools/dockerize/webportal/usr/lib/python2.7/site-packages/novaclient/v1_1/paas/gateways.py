from novaclient import base

class Gateway(base.Resource):
    def delete(self):
        self.manager.delete(self)

    def update(self):
        self.manager.update(self)

class GatewayManager(base.ManagerWithFind):
    resource_class = Gateway

    def get(self, id):
        return self._get('/os-daoli-gateways/%s' % id, 'gateway')

    def list(self):
        return self._list('/os-daoli-gateways', 'gateways')

    def update(self, instance_id, old_gateway, new_gateway):
        body = {"old_gateway": {'hostname': old_gateway},
                "new_gateway": new_gateway}
        return self._update('/os-daoli-gateways/%s' % instance_id, body)
