import logging

from django.utils.translation import ugettext as _

from novaclient.v1_1 import d_groups
from novaclient.v1_1 import d_firewalls
from novaclient.v1_1 import d_gateways

from openstack_dashboard.api.base import APIResourceWrapper
from openstack_dashboard.api.nova import novaclient

LOG = logging.getLogger(__name__)

class Firewall(APIResourceWrapper):
    _attrs = ['id', 'gateway_port', 'service_port', 'instance_id']


# Security Group
def _group(request):
    client = novaclient(request)
    return d_groups.SecurityGroupManager(client)

def security_group_list(request):
    return _group(request).list()

def security_group_update(request, project_id, **kwargs):
    _group(request).update(project_id, **kwargs)

# Firewall

def _firewall(request):
    client = novaclient(request)
    return d_firewalls.FirewallManager(client)

def firewall_create(request, instance_id, hostname, gateway_port, service_port):
    return _firewall(request).create(
        project_id=request.project_id, instance_id=instance_id,
        hostname=hostname, gateway_port=gateway_port, service_port=service_port)

def firewall_list(request):
    return _firewall(request).list()

def firewall_get(request, instance_id):
    return _firewall(request).get(instance_id)

def firewall_delete(request, id):
    _firewall(request).delete(id)

def firewall_exist(request, instance_id, **kwargs):
    return _firewall(request).firewall_exist(instance_id, **kwargs)

# Gateway

def _gateway(request):
    client = novaclient(request)
    return d_gateways.GatewayManager(client)

def gateway_list(request):
   return _gateway(request).list()

def gateway_update(request, instance, old_gateway, gateway):
    return _gateway(request).update(instance, old_gateway, gateway)
