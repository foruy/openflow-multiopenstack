from novaclient import base

class Firewall(base.Resource):
    """A Firewall."""
    def delete(self):
        return self.manager.delete(self)

class FirewallManager(base.Manager):
    resource_class = Firewall

    def get(self, instance):
        return self._list('/os-daoli-firewalls/%s' % base.getid(instance),
                          'firewall')

    def create(self, **kwargs):
        body = {"firewall": kwargs}
        return self._create('/os-daoli-firewalls', body, 'firewall')

    def delete(self, firewall):
        self._delete('/os-daoli-firewalls/%s' % base.getid(firewall))

    def firewall_exist(self, instance_id, **kwargs):
        resp, body = self.api.client.post('/os-daoli-firewalls/%s/action' %
                                          instance_id, body=kwargs)
        return body

    def firewall_update(self, instance_id, **firewall):
       body = {"firewall": firewall}
       return self._update('/os-daoli-firewalls/%s' % instance_id, body)
