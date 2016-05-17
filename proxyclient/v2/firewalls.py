"""
firewalls interface
"""

from proxyclient import base

class Firewall(base.Resource):
    pass

class FirewallManager(base.Manager):
    resource_class = Firewall

    def get(self, id):
        return self._list('/firewalls/%s' % id, 'firewalls')

    def list(self):
        return self._list('/firewalls', 'firewalls')

    def create(self, **kwargs):
        body = {"firewall": kwargs}
        return self._create('/firewalls', body, 'firewall')

    def delete(self, id):
        return self._delete('/firewalls/%s' % id)

    def exists(self, instance_id, **kwargs):
        body = {"firewall": kwargs.copy()}
        return self.api.client.post('/firewalls/%s/action' % instance_id,
                                    body=body)
