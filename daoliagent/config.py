from oslo.config import cfg
from oslo.db import options

from daoliagent import paths
from daoliagent.openstack.common.gettextutils import _
from daoliagent.openstack.common import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

_DEFAULT_SQL_CONNECTION = 'sqlite:///' + paths.state_path_def('daoliproxy.sqlite')

def init(args, **kwargs):
    options.set_defaults(CONF, connection=_DEFAULT_SQL_CONNECTION,
                        sqlite_db='daoliproxy.sqlite')
    cfg.CONF(args=args, project='daoliagent', version='1.0', **kwargs)

def setup_logging():
    """Sets up the logging options for a log with supplied name."""
    product_name = "daoliagent"
    logging.setup(product_name)
    LOG.info(_("Logging enabled!"))
