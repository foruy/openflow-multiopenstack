from oslo_config import cfg
from oslo_log import log as logging

from daoliproxy.agent import base

from novaclient.v2 import client as nova_client

CONF = cfg.CONF

LOG = logging.getLogger(__name__)


def novaclient(request):
    auth_url = base.url_for(request.catalog, 'compute')
    LOG.debug('novaclient connection created using token "%s" and url "%s"' %
              (request.auth_token, auth_url))
    c = nova_client.Client(request.user_name,
                           request.auth_token,
                           project_id=request.project_id,
                           auth_url=auth_url,
                           insecure=False,
                           cacert=None,
                           http_log_debug=CONF.debug)
    c.client.auth_token = request.auth_token
    c.client.management_url = auth_url
    return c

def server_get(request, instance_id):
    return novaclient(request).servers.get(instance_id)

def server_delete(request, instance_id):
    novaclient(request).servers.delete(instance_id)

def server_create(request, name, image, flavor,
                  key_name=None, user_data=None,
                  security_groups=None, block_device_mapping=None,
                  block_device_mapping_v2=None, nics=None,
                  availability_zone=None, instance_count=1, admin_pass=None,
                  disk_config=None):
    return novaclient(request).servers.create(
        name, image, flavor, userdata=user_data,
        security_groups=security_groups,
        key_name=key_name, block_device_mapping=block_device_mapping,
        block_device_mapping_v2=block_device_mapping_v2,
        nics=nics, availability_zone=availability_zone,
        min_count=instance_count, admin_pass=admin_pass,
        disk_config=disk_config)

def server_start(request, instance_id):
    novaclient(request).servers.start(instance_id)

def server_stop(request, instance_id):
    novaclient(request).servers.stop(instance_id)

def flavor_list(request, is_public=True):
    """Get the list of available instance sizes (flavors)."""
    return novaclient(request).flavors.list(is_public=is_public)

def network_list(request):
    return novaclient(request).networks.list()
