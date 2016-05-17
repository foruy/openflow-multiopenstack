"""Generic Node base class for all workers that run on hosts."""

import random

from oslo_concurrency import processutils
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils

from daoliproxy.i18n import _, _LE, _LI, _LW
from daoliproxy.openstack.common import service
from daoliproxy import wsgi
#from daoliproxy.openstack.common import threadgroup
#from daoliproxy.api.router import APIRouter

LOG = logging.getLogger(__name__)

service_opts = [
    cfg.IntOpt('report_interval',
               default=10,
               help='Seconds between nodes reporting state to datastore'),
    cfg.BoolOpt('periodic_enable',
               default=True,
               help='Enable periodic tasks'),
    cfg.IntOpt('periodic_fuzzy_delay',
               default=60,
               help='Range of seconds to randomly delay when starting the'
                    ' periodic task scheduler to reduce stampeding.'
                    ' (Disable by setting to 0)'),
    cfg.IntOpt('timeout',
               default=10,
               help='Request timeout'),
    cfg.StrOpt('daoliproxy_listen',
               default="0.0.0.0",
               help='The IP address on which the metadata API will listen.'),
    cfg.IntOpt('daoliproxy_listen_port',
               default=65534,
               help='The port on which the metadata API will listen.'),
    cfg.IntOpt('daoliproxy_workers',
               help='Number of workers for metadata service. The default will '
                    'be the number of CPUs available.'),
    #cfg.StrOpt('daoliproxy_manager',
    #           default='daoliproxy.manager.ProxyManager',
    #           help='Full class name for the Manager for compute'),
]

CONF = cfg.CONF
CONF.register_opts(service_opts)

class WSGIService(object):
    """Provides ability to launch API from a 'paste' configuration."""

    def __init__(self, name, loader=None, use_ssl=False, max_url_len=None):
        """Initialize, but do not start the WSGI server.

        :param name: The name of the WSGI server given to the loader.
        :param loader: Loads the WSGI application using the given name.
        :returns: None

        """
        self.name = name
        self.manager = self._get_manager()
        self.loader = loader or wsgi.Loader()
        self.app = self.loader.load_app(name)
        #self.app = APIRouter()
        self.host = getattr(CONF, '%s_listen' % name, "0.0.0.0")
        self.port = getattr(CONF, '%s_listen_port' % name, 0)
        self.workers = (getattr(CONF, '%s_workers' % name, None) or
                       processutils.get_worker_count())
        if self.workers and self.workers < 1:
            worker_name = '%s_workers' % name
            msg = (_("%(worker_name)s value of %(workers)s is invalid, "
                     "must be greater than 0") %
                   {'worker_name': worker_name,
                    'workers': str(self.workers)})
            raise exception.InvalidInput(msg)
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

        #self.tg = threadgroup.ThreadGroup(1000)

    def reset(self):
        """Reset server greenpool size to default.

        :returns: None
        """
        self.server.reset()

    def _get_manager(self):
        """Initialize a Manager object appropriate for this service.

        Use the service name to look up a Manager subclass from the
        configuration and initialize an instance. If no class name
        is configured, just return None.

        :returns: a Manager instance, or None.

        """
        fl = '%s_manager' % self.name
        if fl not in CONF:
            return None

        manager_class_name = CONF.get(fl, None)
        if not manager_class_name:
            return None

        manager_class = importutils.import_class(manager_class_name)
        return manager_class()

    def start(self):
        """Start serving this service using loaded configuration.

        Also, retrieve updated port number in case '0' was passed in, which
        indicates a random port should be used.

        :returns: None

        """
        if self.manager:
            self.manager.init_host()
            self.manager.pre_start_hook()
            if self.backdoor_port is not None:
                self.manager.backdoor_port = self.backdoor_port
        self.server.start()
        if self.manager:
            self.manager.post_start_hook()

    def stop(self):
        """Stop serving this API.

        :returns: None

        """
        self.server.stop()

    def wait(self):
        """Wait for the service to stop serving this API.

        :returns: None
        """
        self.server.wait()

def process_launcher():
    return service.ProcessLauncher()


_launcher = None

def serve(server, workers=None):
    global _launcher
    if _launcher:
        raise RuntimeError(_('serve() can only be called once'))

    _launcher = service.launch(server, workers=workers)

def wait():
    _launcher.wait()
