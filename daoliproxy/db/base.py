from oslo_config import cfg
from oslo_utils import importutils


db_driver_opt = cfg.StrOpt('db_driver',
                           default='daoliproxy.db',
                           help='The driver to use for database access')

CONF = cfg.CONF
CONF.register_opt(db_driver_opt)
CONF.register_opt(cfg.IntOpt('auth_expires', default=3600))

class Base(object):
    """DB driver is injected in the init method."""

    def __init__(self, db_driver=None):
        super(Base, self).__init__()
        if not db_driver:
            db_driver = CONF.db_driver
        self.db = importutils.import_module(db_driver)
