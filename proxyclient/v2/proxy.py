from proxyclient import base

class Proxy(base.Resource):
    pass

class ProxyManager(base.Manager):

    resource_class = Proxy

    def authenticate_by_zone(self, user_id, zone_id):
        body = {"auth": {"zone_id": zone_id}}
        return self._update('/os-proxy/authenticate/%s' % user_id, body)

    def register(self, user_id, zone_id):
        body = {"auth": {"user_id": user_id, "zone_id": zone_id}}
        return self._create('/os-proxy/users/register', body, 'user')

    def resetpassword(self, **auth):
        body = {"auth": auth}
        return self._update('/os-proxy/os-password/resetpassword', body)

    def flavor_rebuild(self, body):
        return self._update('/os-proxy/flavors', body)

    def network_rebuild(self, body):
        return self._update('/os-proxy/networks', body)

    def gateway_rebuild(self, body):
        return self._update('/os-proxy/gateways', body)

    def image_rebuild(self, body):
        return self._update('/os-proxy/images', body)

    def zone_create(self, body):
        return self._create('/os-proxy/zones', body, 'zone')

    def server_create(self, base, server, kwargs):
        body = {"base": base, "server": server, "kwargs": kwargs}
        return self._create('/os-proxy/servers', body, 'server'}

    def server_delete(self, id):
        self._delete('/os-proxy/servers/%s' % id)

    def server_start(self, id):
        self._action('os-start-proxy', id)

    def server_stop(self, id):
        self._action('os-stop-proxy', id)

    def _action(self, action, id, info=None, **kwargs):
        """
        Perform a server "action" -- start/stop/etc.
        """
        body = {action: info}
        url = '/os-proxy/servers/%s/action' % instance_id
        _resp, body = self.api.client.post(url, body=body)
        return body
