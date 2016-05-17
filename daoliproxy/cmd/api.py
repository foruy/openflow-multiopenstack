"""Starter script for Daoliproxy API."""

import eventlet
eventlet.monkey_patch(thread=False)

import sys

from oslo_config import cfg
from oslo_log import log as logging

from daoliproxy import config
from daoliproxy.openstack.common.report import guru_meditation_report as gmr
from daoliproxy import service
from daoliproxy import utils
from daoliproxy import version

CONF = cfg.CONF

def main():
    config.parse_args(sys.argv)
    logging.setup(CONF, "daoliproxy")
    utils.monkey_patch()

    gmr.TextGuruMeditation.setup_autorun(version)

    launcher = service.process_launcher()
    server = service.WSGIService('daoliproxy')
    launcher.launch_service(server, workers=1)
    #launcher.launch_service(server, workers=server.workers or 1)
    launcher.wait()

if __name__ == '__main__':
    main()
