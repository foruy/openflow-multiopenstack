"""
user interface """

from proxyclient import base

class User(base.Resource):
    def __repr__(self):
        return "<User: %s>" % self.username


class UserManager(base.Manager):
    resource_class = User

    def authenticate(self, username, password, **kwargs):
        body = {"auth": {"username": username, "password": password},
                "kwargs": kwargs}
        return self._create('/authenticate', body, 'user')

    def authenticate_by_zone(self, user_id, zone_id):
        body = {"auth": {"zone_id": zone_id}}
        return self._update('/authenticate/%s' % user_id, body)

    def user_absolute_limits(self, zone_id=None):
        query_string = '?zone_id=%s' % zone_id if zone_id else ''
        return self._get('/limits%s' % query_string, 'limits')

    def list(self):
        return self._list('/users', 'users')

    def get(self, id):
        return self._get('/users/%s' % id, 'user')

    def delete(self, id):
        return self._delete('/users/%s' % id)

    def check(self, key, val):
        return self._action('os-check', {key: val})

    def register(self, **kwargs):
        body = {"auth": kwargs}
        return self._create('/users/register', body, 'user')

    def _action(self, action, info=None, **kwargs):
        data = {action: info}
        self.api.client.put('/users/action', body=data)

    def validate(self, **kwargs):
        body = {"user": dict((k, v) for k, v in kwargs.items() if v)}
        return self._update('/os-password', body)

    def update_key(self, username, email, **kwargs):
        body = {"user": {"base": {"username": username, "email": email}}}
        body["user"]["kwargs"] = kwargs
        return self._update('/os-password/userkey', body)

    def getpassword(self, id, username, email, **kwargs):
        body = {"user": {"base": {"id": id, "username": username, "email": email},
                         "kwargs": kwargs}}
        return self._update('/os-password/getpassword', body)

    def resetpassword(self, id, username, email, **kwargs):
        body = {"user": {"base": {"id": id, "username": username, "email": email},
                         "kwargs": kwargs}}
        return self._update('/os-password/resetpassword', body)

    def login_list(self, user_id=None):
        query_string = "?user_id=%s" % user_id if user_id else ""
        return self._list('/user_login%s' % query_string, 'users')
