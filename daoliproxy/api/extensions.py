
from oslo_config import cfg
from oslo_log import log as logging

from daoliproxy.api.openstack import extensions as base_extensions

ext_opts = [
    cfg.MultiStrOpt('osapi_proxy_extension',
                    default=[],
                    help='osapi proxy extension to load'),
]
CONF = cfg.CONF
CONF.register_opts(ext_opts)

LOG = logging.getLogger(__name__)


class ExtensionManager(base_extensions.ExtensionManager):
    def __init__(self):
        self.cls_list = CONF.osapi_proxy_extension
        self.extensions = {}
        self.sorted_ext_list = []
        self._load_extensions()
