from django.conf import settings

from proxyclient.v1 import client as proxy_client

from openstack_dashboard.api import base

def proxyclient(request):
    management_url = getattr(settings, 'MANAGEMENT_URL')
    conn = proxy_client.Client(http_log_debug=True)
    conn.set_management_url(management_url)
    return conn

def _proxy(request):
    return proxyclient(request).proxy

def availability_zone_list(request, detail=False):
    user_id = request.user.id if not detail else None
    return _proxy(request).availability_zone_list(user_id=user_id)

def availability_zone_get(request, id):
    return _proxy(request).availability_zone_get(id)

def authenticate(request, username, password, **kwargs):
    return _proxy(request).authenticate(username, password, **kwargs)

def authenticate_by_zone(request, zone_id):
    return _proxy(request).authenticate_by_zone(request.user.id, zone_id)

def logout(request):
    _proxy(request).logout(request.user.id)

def flavor_list(request, zone_id): #cg
    return _proxy(request).flavor_list(zone_id)

def image_list_detailed(request, zone_id, filters=None): #cg
    images = _proxy(request).image_list_detailed(zone_id, filters=filters)
    return images, False

def project_absolute_limits(request, zone_id):
    return _proxy(request).project_absolute_limits(request.user.id, zone_id)

def user_absolute_limits(request):
    return _proxy(request).user_absolute_limits(request.user.id)

def server_get(request, instance_id):
    return _proxy(request).server_get(instance_id)

def server_list(request, all_tenants=False):
    return _proxy(request).server_list(request.user.id, all_tenants=all_tenants)

def server_delete(request, instance_id):
    _proxy(request).server_delete(request.user.id, instance_id)

def server_start(request, instance_id):
    _proxy(request).server_start(instance_id)

def server_stop(request, instance_id):
    _proxy(request).server_stop(instance_id)

def server_create(request, name, image, flavor, zone_id=None,
                  key_name=None, user_data=None, security_groups=None,
                  block_device_mapping=None, block_device_mapping_v2=None, nics=None,
                  availability_zone=None, instance_count=1, admin_pass=None,
                  disk_config=None, accessIPv4=None, gateway=None, net_type=None): #cg
    return _proxy(request).server_create(
        request.user.id, name, image, flavor, zone_id=zone_id,
        user_data=user_data, security_groups=security_groups,
        key_name=key_name, block_device_mapping=block_device_mapping,
        block_device_mapping_v2=block_device_mapping_v2,
        nics=nics, availability_zone=availability_zone,
        instance_count=instance_count, admin_pass=admin_pass,
        disk_config=disk_config, accessIPv4=accessIPv4,
        gateway=gateway, net_type=net_type)

def firewall_get(request, instance_id):
    return _proxy(request).firewall_get(instance_id)

def firewall_delete(request, firewall_id):
    _proxy(request).firewall_delete(firewall_id)

def firewall_create(request, instance_id, hostname, gateway_port, service_port):
    return _proxy(request).firewall_create(
        instance_id=instance_id, hostname=hostname,
        gateway_port=gateway_port, service_port=service_port)

def firewall_exist(request, instance_id, hostname=None, gateway_port=None):
    return _proxy(request).firewall_exist(
        instance_id, hostname=hostname, gateway_port=gateway_port)

def gateway_list(request):
    return _proxy(request).gateway_list()

def gateway_get(request, id):
    return _proxy(request).gateway_get(id)

def gateway_get_by_instance(request, instance_id):
    return _proxy(request).gateway_get_instance(instance_id)

def gateway_update(request, id, **kwargs):
    return _proxy(request).gateway_update(id, **kwargs)

def security_group_list(request):
    return _proxy(request).security_group_list(request.user.id)

def security_group_update(request, **kwargs):
    _proxy(request).security_group_update(request.user.id, **kwargs)

# User
def user_list(request):
    return _proxy(request).user_list(request.user.id)

def user_get(request, user_id):
    return _proxy(request).user_get(user_id)

def register(request, **values):
    return _proxy(request).register(**values)

def checkdata(request, key, val):
    return _proxy(request).check_data(key, val)

def user_login_list(request):
    return _proxy(request).user_login_list(request.user.id)

def user_login_get(request, user_id=None):
    user_id = user_id or request.user.id
    return _proxy(request).user_login_get(user_id)

def server_network(request, address=None):
    return _proxy(request).server_network(request.user.id, address=address)

def image_get(request, zone):
    return _proxy(request).image_get(zone)

def image_delete(request, image_id):
    return _proxy(request).image_delete(image_id)

def image_rebuild(request, zone):
    return _proxy(request).image_rebuild(request.user.id, zone)

def zone_create(request, id=None, name=None, auth_url=None,
                token=None, default_instances=None):
    #return _proxy(request).zone_create(request.user.id, id=id, name=name,
    return _proxy(request).zone_create(request.user.id, name=name,
                                       auth_url=auth_url, token=token,
                                       default_instances=default_instances)

def zone_delete(request, zone_id):
    _proxy(request).zone_delete(zone_id)

def flavor_get_by_zone(request, zone_id):
    return _proxy(request).flavor_get_by_zone(zone_id)

def flavor_delete(request, zone_id):
    _proxy(request).flavor_delete(zone_id)

def flavor_rebuild(request, zone):
    return _proxy(request).flavor_rebuild(request.user.id, zone)

def gateway_get_by_zone(request, zone_id):
    return _proxy(request).gateway_get_by_zone(zone_id)

def gateway_delete(request, zone_id):
    _proxy(request).gateway_delete(zone_id)

def gateway_rebuild(request, zone):
    return _proxy(request).gateway_rebuild(request.user.id, zone)

# Deprecated
def get_last_network_type(request):
    return _proxy(request).get_last_network_type(request.user.id)

def network_list(request):
    return _proxy(request).network_list()

def network_get_by_zone(request, zone_id):
    return _proxy(request).network_get_by_zone(zone_id)

def network_rebuild(request, zone):
    return _proxy(request).network_rebuild(request.user.id, zone)

def network_delete(request, network_id):
    _proxy(request).network_delete(network_id)

def network_type_list(request):
    return _proxy(request).network_type_list()

def network_type_delete(request, id):
    _proxy(request).network_type_delete(id)

def resource_list(request, user_id=None):
    return _proxy(request).resource_list(user_id or request.user.id)

def resource_get(request, user_id=None, source_name=None, source_id=None):
    filters = {'source_id': source_id, 'source_name': source_name}
    return _proxy(request).resource_get(user_id or request.user.id,
                                        filters=filters)

def user_get_by_time(request, start_time=None, end_time=None):
    return _proxy(request).user_get_by_time(
        request.user.id, start_time=start_time, end_time=end_time)

def validate_user(request, username=None, password=None, email=None):
    return _proxy(request).validate_user(
        username=username, password=password, email=email)

def update_user_key(request, username, email, url=None, key=None):
    return _proxy(request).update_user_key(username, email, url=url, key=key)

def getpassword(request, id, username, email, key=None):
    return _proxy(request).getpassword(id, username, email, key=key)

def resetpassword(request, id, username, email, key=None, password=None):
    return _proxy(request).resetpassword(
            id, username, email, key=key, password=password)

def user_delete(request, user_id):
    return _proxy(request).user_delete(request.user.id, user_id)

def get_monitor(request, instance):
    return _proxy(request).get_monitor(instance)

def device_get(request, gateway_id):
    return _proxy(request).device_get(gateway_id)
