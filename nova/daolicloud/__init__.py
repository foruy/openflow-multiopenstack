import sys

from oslo_config import cfg
from oslo_log import log as logging

from nova import utils
from nova import config
from nova import objects
from nova import version
from nova.daolicloud import service
from nova.openstack.common.report import guru_meditation_report as gmr

CONF = cfg.CONF

def main():
    config.parse_args(sys.argv)
    logging.setup(CONF, "nova")
    utils.monkey_patch()
    objects.register_all()

    gmr.TextGuruMeditation.setup_autorun(version)

    launcher = service.process_launcher()
    server = service.Service('daolisync')
    launcher.launch_service(server)
    launcher.wait()
