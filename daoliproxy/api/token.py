import hashlib
import collections

from oslo.config import cfg

from daoliproxy import utils

from keystoneclient.v2_0 import client as client_v2
from keystoneclient.v3 import client as client_v3

keystone_opts = [
    cfg.FloatOpt('identity_version', default=2.0),
    cfg.StrOpt('keystone_url', default='http://127.0.0.1:5000/v$identity_version'),
]

CONF = cfg.CONF
CONF.register_opts(keystone_opts)

class Token(object):
    def __init__(self, auth_ref, **kwargs):
        self.id = auth_ref.auth_token

        if len(self.id) > 64:
            algorithm = 'md5'
            hasher = hashlib.new(algorithm)
            hasher.update(self.id)
            self.id = hasher.hexdigest()

        self.expires = auth_ref.expires
        self.user_id = auth_ref.user_id
        self.project_id = auth_ref.project_id
        self.host = kwargs.get('host', None)

        if CONF.identity_version < 3:
            self._catalog = auth_ref.get('serviceCatalog', [])
        else:
            self._catalog = auth_ref.get('catalog', [])

    @property
    def catalog(self):
        service = {}
        for cat in self._catalog:
            for endpoint in cat['endpoints']:
                url = endpoint['publicURL']
                if self.host:
                    url = utils.replace_url(url, self.host)
                service[cat['type']] = {'name': cat['name'], 'publicURL': url}
        return service


def get_keystone_client():
    if CONF.identity_version < 3:
        return client_v2
    else:
        return client_v3

def authentication(username, password, auth_url=None):
    if auth_url is None:
        auth_url = CONF.default_keystone_url

    client = get_keystone_client().Client(username=username,
                                          password=password,
                                          project_name=username,
                                          auth_url=auth_url,
                                          debug=CONF.debug,
                                          timeout=CONF.timeout)
    host = utils.urlparse.urlparse(auth_url).hostname
    return Token(client.auth_ref, host=host)
