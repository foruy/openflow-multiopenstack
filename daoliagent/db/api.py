from oslo.config import cfg
from oslo.db import concurrency

CONF = cfg.CONF

_BACKEND_MAPPING = {'sqlalchemy': 'daoliagent.db.sqlalchemy.api'}

IMPL = concurrency.TpoolDbapiWrapper(CONF, backend_mapping=_BACKEND_MAPPING)

def server_get(id, gateway=False):
    return IMPL.server_get(id, gateway=gateway)

def server_get_by_mac(macaddr, ipaddr, group=True):
    return IMPL.server_get_by_mac(macaddr, ipaddr, group=group)

def gateway_get_all():
    return IMPL.gateway_get_all()

def gateway_get_by_name(hostname):
    return IMPL.gateway_get_by_filter(hostname=hostname)

def gateway_get_by_datapath(datapath_id):
    return IMPL.gateway_get_by_filter(datapath_id=datapath_id)

def gateway_get_by_idc(idc_id):
    return IMPL.gateway_get_by_idc(idc_id)

def firewall_get_by_packet(hostname, dst_port):
    return IMPL.firewall_get_by_packet(hostname, dst_port)
