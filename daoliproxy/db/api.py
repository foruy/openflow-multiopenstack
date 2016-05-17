"""Defines interface for DB access.

All functions in this module return objects that implement a dictionary-like
interface. Currently, many of these objects are sqlalchemy objects that
implement a dictionary interface. However, a future goal is to have all of
these objects be simple dictionaries.
"""

from oslo_config import cfg
from oslo_db import concurrency
from oslo_log import log as logging

from daoliproxy.i18n import _LE

CONF = cfg.CONF

_BACKEND_MAPPING = {'sqlalchemy': 'daoliproxy.db.sqlalchemy.api'}

IMPL = concurrency.TpoolDbapiWrapper(CONF, backend_mapping=_BACKEND_MAPPING)

LOG = logging.getLogger(__name__)

def authenticate(context, username, password, **kwargs):
    return IMPL.authenticate(context, username, password, **kwargs)

def user_token_create(context, user_id, token=None):
    return IMPL.user_token_create(context, user_id, token=token)

def keystone_token_create(context, **values):
    return IMPL.keystone_token_create(context, **values)

def user_absolute_limits(context, user_id, zone_id=None):
    return IMPL.user_absolute_limits(context, user_id, zone_id=zone_id)


def user_token_get(context, token):
    return IMPL.user_token_get(context, token)

def keystone_token_get(context, token):
    return IMPL.keystone_token_get(context, token)

def zone_get(context, id):
    return IMPL.zone_get(context, id)

def zone_get_all(context, idc_id=None, disabled=True):
    return IMPL.zone_get_all(context, idc_id=idc_id, disabled=disabled)

def zone_create(context, values):
    return IMPL.zone_create(context, values)

def zone_delete(context, id):
    IMPL.zone_delete(context, id)

def zone_update(context, id, values):
    return IMPL.zone_update(context, id, values)

def zone_exists(context, auth_url=None):
    return IMPL.zone_exists(context, auth_url=auth_url)

def zone_get_by_image(context, image_id, zones):
    return IMPL.zone_get_by_image(context, image_id, zones)

def user_get(context, id):
    return IMPL.user_get(context, id)

def user_get_all(context):
    return IMPL.user_get_all(context)

def user_delete(context, id):
    return IMPL.user_delete(context, id)

def user_check(context, key, val):
    return IMPL.user_check(context, key, val)

def user_task(context, utype, uobj):
    return IMPL.user_task(context, utype, uobj)

def register(context, **values):
    return IMPL.register(context, **values)

def validate_user(context, user):
    return IMPL.validate_user(context, user)

def update_user(context, base, **values):
    return IMPL.update_user(context, base, **values)

def user_login_list(context, user_id=None):
    return IMPL.user_login_list(context, user_id=user_id)


def service_get_by_idc(context, idc_id):
    return IMPL.service_get_by_idc(context, idc_id)

def service_create(context, values):
    return IMPL.service_create(context, values)

def server_get_all(context, user_id=None):
    return IMPL.server_get_all(context, user_id=user_id)

def server_get(context, id):
    return IMPL.server_get(context, id)

def server_get_by_zone(context, zone_id):
    return IMPL.server_get_by_zone(context, zone_id)

def address_filter(context, user_id, address):
    return IMPL.address_filter(context, user_id, address)

def server_create(context, values):
    return IMPL.server_create(context, values)

def server_delete(context, id):
    return IMPL.server_delete(context, id)

def server_update(context, id, values):
    return IMPL.server_update(context, id, values)

def role_get_by_name(context, user_id):
    return IMPL.role_get_by_name(context, user_id)

def image_get_all(context, zone_id=None):
    return IMPL.image_get_all(context, zone_id=zone_id)

def image_get(context, image_id):
    return IMPL.image_get(context, image_id)

def image_delete(context, id=None, zone_id=None):
    return IMPL.image_delete(context, id=id, zone_id=zone_id)

def image_create(context, zone_id, values):
    return IMPL.image_create(context, zone_id, values)

def flavor_get(context, id, zone_id=None):
    return IMPL.flavor_get(context, id, zone_id=zone_id)

def flavor_get_all(context, zone_id=None):
    return IMPL.flavor_get_all(context, zone_id=zone_id)

def flavor_delete(context, id=None, zone_id=None):
    return IMPL.flavor_delete(context, id=id, zone_id=zone_id)

def flavor_create(context, zone_id, values):
    return IMPL.flavor_create(context, zone_id, values)

def gateway_get_all(context, zone_id=None):
    return IMPL.gateway_get_all(context, zone_id=zone_id)

def gateway_get_by_idc(context, idc_id):
    return IMPL.gateway_get_by_idc(context, idc_id)

def gateway_get(context, hostname):
    return IMPL.gateway_get(context, hostname)

def gateway_delete(context, id=None, zone_id=None):
    return IMPL.gateway_delete(context, id=id, zone_id=zone_id)

def gateway_create(context, zone_id, values):
    return IMPL.gateway_create(context, zone_id, values)

def gateway_count(context, hostname):
    return IMPL.gateway_count(context, hostname)

def gateway_get_by_idc(context, idc_id):
    return IMPL.gateway_get_by_idc(context, idc_id)


# Network

def network_get(context, net_id=None, zone_id=None):
    return IMPL.network_get(context, net_id=net_id, zone_id=zone_id)

def network_get_all(context, zone_id=None):
    return IMPL.network_get_all(context, zone_id=zone_id)

def network_delete(context, id=None, zone_id=None):
    return IMPL.network_delete(context, id=id, zone_id=zone_id)

def network_create(context, zone_id, values):
    return IMPL.network_create(context, zone_id, values)

def network_type_list(context):
    return IMPL.network_type_list(context)

def network_type_update(context, cidr):
    return IMPL.network_type_update(context, cidr)

def network_type_delete(context, id):
    IMPL.network_type_delete(context, id)

def generate_ip(context, user_id, netype):
    return IMPL.generate_ip(context, user_id, netype)

def security_group_get(context, user_id):
    return IMPL.security_group_get(context, user_id)

def security_group_list(context):
    return IMPL.security_group_list(context)

def security_group_create(context, user_id, start, end):
    return IMPL.security_group_create(context, user_id, start, end)

def security_group_delete(context, user_id, start, end):
    return IMPL.security_group_delete(context, user_id, start, end)

def firewall_get(context, id=None, hostname=None, gateway_port=None):
    return IMPL.firewall_get(context, id=id,
            hostname=hostname, gateway_port=gateway_port)

def firewall_get_by_instance(context, instance_id):
    return IMPL.firewall_get_by_instance(context, instance_id)

def firewall_create(context, values):
    return IMPL.firewall_create(context, values)

def firewall_delete(context, id):
    IMPL.firewall_delete(context, id)


def resource_get(context, user_id=None, source_id=None, source_name=None):
    return IMPL.resource_get(context, user_id=user_id,
                             source_id=source_id, source_name=source_name)

def resource_create(context, source_name, source_id, action, user_id,
                    extra=None):
    return IMPL.resource_create(context, source_name, source_id, action, user_id,
                                extra=extra)
