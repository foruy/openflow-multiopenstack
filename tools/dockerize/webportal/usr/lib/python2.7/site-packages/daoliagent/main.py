import sys

from oslo.config import cfg

from ryu.base.app_manager import AppManager
from ryu import cfg as ryu_cfg
from ryu.lib import hub
hub.patch()

from daoliagent import config

DEFAULT_CONFIG = ["/etc/daoliproxy/daoliproxy.conf"]

def main():
    config.init(sys.argv[1:], default_config_files=DEFAULT_CONFIG)
    if ryu_cfg.CONF is not cfg.CONF:
        ryu_cfg.CONF(project='ryu', args=[])
    config.setup_logging()
    AppManager.run_apps(['daoliagent.ofa_agent'])

if __name__ == '__main__':
    main()
