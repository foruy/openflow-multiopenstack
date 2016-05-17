from django.conf import settings

#from proxyclient.v2 import client as proxy_client
from openstack_dashboard.utils import proxy_client


def proxyclient(request):
    management_url = getattr(settings, 'MANAGEMENT_URL')
    conn = proxy_client.Client(request.user.username,
                               request.user.token.id,
                               user_id=request.user.id,
                               project_id=request.user.project_id,
                               insecure=False,
                               cacert=None,
                               http_log_debug=settings.DEBUG)
    conn.client.auth_token = request.user.token.id
    conn.client.set_management_url(management_url)
    return conn

def authenticate(request, username, password, **kwargs):
    return proxyclient(request).users.authenticate(username, password, **kwargs)

def authenticate_by_zone(request, zone_id):
    return proxyclient(request).users.authenticate_by_zone(request.user.id, zone_id)

def user_list(request):
    return proxyclient(request).users.list()

def user_get(request):
    return proxyclient(request).users.get(request.user.id)

def user_delete(request, user_id):
    return proxyclient(request).users.delete(user_id)

def user_login_list(request, user_id=None):
    return proxyclient(request).users.login_list(user_id=user_id)

def availability_zone_list(request, detail=False):
    return proxyclient(request).zones.list(detail=detail)

def availability_zone_get(request, id):
    return proxyclient(request).zones.get(id)

def zone_create(request, id=None, name=None, auth_url=None,
                auth_token=None, default_instances=None):
    return proxyclient(request).zones.create(
            id=id, name=name, auth_url=auth_url, auth_token=auth_token,
            default_instances=default_instances)

def zone_delete(request, zone_id):
    proxyclient(request).zones.delete(zone_id)
#
#def logout(request):
#    _proxy(request).logout(request.user.id)

def server_list(request, all_tenants=False):
    return proxyclient(request).servers.list(all_tenants=all_tenants)

def server_get(request, instance_id):
    return proxyclient(request).servers.get(instance_id)

def server_create(request, name, image, flavor, zone_id=None,
                  key_name=None, user_data=None, security_groups=None,
                  block_device_mapping=None, block_device_mapping_v2=None, nics=None,
                  availability_zone=None, instance_count=1, admin_pass=None,
                  disk_config=None, accessIPv4=None, gateway=None, net_type=None): #cg
    return proxyclient(request).servers.create(
        name, image, flavor, zone_id=zone_id,
        user_data=user_data, security_groups=security_groups,
        key_name=key_name, block_device_mapping=block_device_mapping,
        block_device_mapping_v2=block_device_mapping_v2,
        nics=nics, availability_zone=availability_zone,
        instance_count=instance_count, admin_pass=admin_pass,
        disk_config=disk_config, accessIPv4=accessIPv4,
        gateway=gateway, netype=net_type)

def server_delete(request, instance_id):
    proxyclient(request).servers.delete(instance_id)

def server_start(request, instance_id):
    proxyclient(request).servers.start(instance_id)

def server_stop(request, instance_id):
    proxyclient(request).servers.stop(instance_id)


def image_list_detailed(request, zone_id, filters=None):
    return image_get(request, zone_id, filters=filters), False

def image_get(request, zone, filters=None):
    return proxyclient(request).images.get(zone, filters=filters)

def image_delete(request, image_id):
    proxyclient(request).images.delete(image_id)

def image_rebuild(request, zone):
    return proxyclient(request).images.rebuild(zone)

def flavor_list(request, zone):
    return proxyclient(request).flavors.get(zone)

def flavor_get_by_zone(request, zone):
    return proxyclient(request).flavors.get(zone)

def flavor_delete(request, flavor_id):
    proxyclient(request).flavors.delete(flavor_id)

def flavor_rebuild(request, zone):
    return proxyclient(request).flavors.rebuild(zone)


def gateway_list(request):
    return proxyclient(request).gateways.list()

def gateway_get(request, instance_id):
    return proxyclient(request).gateways.get_by_instance(instance_id)

def gateway_get_by_zone(request, zone):
    return proxyclient(request).gateways.get_by_zone(zone)

def gateway_delete(request, gateway_id):
    proxyclient(request).gateways.delete(gateway_id)

def gateway_rebuild(request, zone):
    return proxyclient(request).gateways.rebuild(zone)


def network_get_by_zone(request, zone):
    return proxyclient(request).networks.get(zone)

def network_delete(request, network_id):
    proxyclient(request).networks.delete(network_id)

def network_rebuild(request, zone):
    return proxyclient(request).networks.rebuild(zone)

def network_type_list(request):
    return proxyclient(request).networks.network_type_list()

def network_type_delete(request, id):
    proxyclient(request).networks.network_type_delete(id)


def security_group_list(request):
    return proxyclient(request).security_groups.list()

def security_group_update(request, **kwargs):
    proxyclient(request).security_groups.update(**kwargs)


def firewall_list(request):
    return proxyclient(request).firewalls.list()

def firewall_get(request, id):
    return proxyclient(request).firewalls.get(id)

def firewall_create(request, instance_id, hostname, gateway_port,
                    service_port):
    return proxyclient(request).firewalls.create(
        instance_id=instance_id, hostname=hostname,
        gateway_port=gateway_port, service_port=service_port)

def firewall_exist(request, instance_id, hostname=None, gateway_port=None):
    return proxyclient(request).firewalls.exists(
        instance_id, hostname=hostname, gateway_port=gateway_port)

def firewall_delete(request, firewall_id):
    proxyclient(request).firewalls.delete(firewall_id)

#
def project_absolute_limits(request, zone_id):
    return proxyclient(request).users.user_absolute_limits(zone_id)

def user_absolute_limits(request):
    return proxyclient(request).users.user_absolute_limits()


def resource_list(request, user_id=None):
    return proxyclient(request).resources.list(
        user_id=user_id or request.user.id)

def resource_get(request, user_id=None, source_name=None, source_id=None):
    filters = {'source_id': source_id, 'source_name': source_name}
    return proxyclient(request).resources.get(
            user_id or request.user.id, filters=filters)

def get_monitor(request, instance):
    return proxyclient(request).servers.monitor(instance)
