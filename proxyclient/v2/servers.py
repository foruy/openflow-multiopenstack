"""
servers interface.
"""

from proxyclient import base

class Server(base.Resource):
    def __repr__(self):
        return "<Server: %s>" % self.name

class ServerManager(base.Manager):
    resource_class = Server

    def list(self, all_tenants=False):
        detail = "/detail" if all_tenants else ""
        return self._list('/servers%s' % detail, 'servers')

    def get(self, instance_id):
        return self._get('/servers/%s'% instance_id, 'server')

    def create(self, name, image, flavor, zone_id=None, **kwargs):
        body = {"server": {"name": name, "image": image, "flavor": flavor}}

        body["kwargs"] = kwargs
        body["kwargs"].setdefault("zone_id", zone_id)

        return self._create('/servers', body, 'server')

    def delete(self, instance_id):
        self._delete('/servers/%s' % instance_id)

    def start(self, instance_id):
        self._action('os-start', instance_id)

    def stop(self, instance_id):
        self._action('os-stop', instance_id)

    def monitor(self, instance_id):
        return self._action('os-monitor', instance_id)[1]

    def _action(self, action, instance_id, info=None, **kwargs):
        """
        Perform a server "action" -- start/stop/etc.
        """
        body = {action: info}
        url = '/servers/%s/action' % instance_id
        _resp, body = self.api.client.post(url, body=body)
        return body
