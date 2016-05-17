from oslo_config import cfg
from oslo_log import log as logging
from oslo_concurrency import processutils

from nova import wsgi
from nova.service import WSGIService
from nova.service import process_launcher
from nova.daolicloud.api.router import APIRouter

service_opts = [
    cfg.StrOpt('daolinat_listen',
               default="0.0.0.0",
               help='The IP address on which the Openstack API will listen.'),
    cfg.IntOpt('daolinat_listen_port',
               default=65535,
               help='The port on which the Openstack API will listen.'),
    cfg.IntOpt('daolinat_workers',
               help='Number of workers for DaoliNat service. The default '
                    'will be the number of CPUs available.')
]

CONF = cfg.CONF
CONF.register_opts(service_opts)

LOG = logging.getLogger(__name__)

class Service(WSGIService):

    def __init__(self, name, loader=None, use_ssl=False, max_url_len=None):
        """Initialize, but do not start the WSGI server.

        :param name: The name of the WSGI server given to the loader.
        :param loader: Loads the WSGI application using the given name.
        """
        self.name = name
        self.manager = self._get_manager()
        self.app = APIRouter()
        self.host = getattr(CONF, '%s_listen' % name, "0.0.0.0")
        self.port = getattr(CONF, '%s_listen_port' % name, 65535)
        self.workers = (getattr(CONF, '%s_workers' % name, None) or
                        processutils.get_worker_count())
        self.use_ssl = use_ssl
        self.server = wsgi.Server(name,
                                  self.app,
                                  host=self.host,
                                  port=self.port,
                                  use_ssl=self.use_ssl,
                                  max_url_len=max_url_len)

        # Pull back actual port used
        self.port = self.server.port
        self.backdoor_port = None
