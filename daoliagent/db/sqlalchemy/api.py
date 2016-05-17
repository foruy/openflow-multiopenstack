"""Implementation of SQLAlchemy backend."""
import sys
import threading

from oslo.config import cfg
from oslo.db.sqlalchemy import session as db_session
from sqlalchemy import and_, or_

from daoliagent.openstack.common import log as logging
from daoliagent.db.sqlalchemy import models

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

_ENGINE_FACADE = None
_LOCK = threading.Lock()

def _create_facade_lazily():
    global _LOCK, _ENGINE_FACADE
    if _ENGINE_FACADE is None:
        with _LOCK:
            if _ENGINE_FACADE is None:
                _ENGINE_FACADE = db_session.EngineFacade.from_config(CONF)
    return _ENGINE_FACADE

def get_engine(use_slave=False):
    facade = _create_facade_lazily()
    return facade.get_engine(use_slave=use_slave)

def get_session(use_slave=False, **kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(use_slave=use_slave, **kwargs)

def get_backend():
    """The backend is this module itself."""
    return sys.modules[__name__]

def model_query(model, *args, **kwargs):
    session = kwargs.get('session') or get_session()
    query = session.query(model, *args)
    return query

def server_get(id, gateway=False, session=None):
    session = session or get_session()
    tables = [models.Instance]
    if gateway:
        tables.append(models.Gateway)

    query = model_query(*tables, session=session)

    if gateway:
        query = query.join(models.Gateway, models.Gateway.hostname==models.Instance.host)

    result = query.filter(models.Instance.id==id).first()
    if result:
        instance_network = model_query(models.InstanceNetwork, session=session). \
                filter_by(instance_id=result.Instance.id).first()
                
        if not instance_network:
            return None
            
        result.Instance.address = instance_network['address']
        result.Instance.mac_address = instance_network['mac_address']

    return result

def server_get_by_mac(macaddr, ipaddr, group=True):
    session = get_session()
    data = {'has_more': False, 'src': None, 'dst': None}
    query = model_query(models.Instance.id, models.Instance.host,
                        models.Instance.user_id, models.Instance.host,
                        models.InstanceNetwork.address,
                        models.InstanceNetwork.mac_address,
                        session=session).filter(
            models.Instance.id==models.InstanceNetwork.instance_id)

    src = query.filter(models.InstanceNetwork.mac_address==macaddr).first()
    
    if src is not None:
        data['src'] = src
        dst = query.filter(models.InstanceNetwork.address==ipaddr,
                           models.Instance.user_id==src.user_id).first()
        if dst is not None:
            data['dst'] = dst
            if group: 
                query = model_query(models.SingleSecurityGroup,
                                    session=session).filter(or_(
                        and_(models.SingleSecurityGroup.start==src.id,
                             models.SingleSecurityGroup.end==dst.id),
                        and_(models.SingleSecurityGroup.start==dst.id,
                             models.SingleSecurityGroup.end==src.id)))
                if query.first():
                    data['has_more'] = True
    return data

def gateway_get_by_filter(datapath_id=None, hostname=None):
    query = model_query(models.Gateway)

    if datapath_id is not None:
        query = query.filter_by(datapath_id=datapath_id)

    if hostname is not None:
        query = query.filter_by(hostname=hostname)

    return query.first()

def gateway_get_all():
    return model_query(models.Gateway).all()

def gateway_get_by_idc(idc_id):
    query = model_query(models.Gateway).filter_by(idc_id=idc_id)

    _query = query.filter(or_(
                models.Gateway.vext_ip!=models.Gateway.ext_ip,
                models.Gateway.int_dev!=models.Gateway.ext_dev))

    result = _query.filter_by(disabled=False).all()

    if not result:
        result = query.all()

    return result

def firewall_get_by_packet(hostname, dst_port):
    session = get_session()
    query = model_query(models.Instance, models.Gateway,
                        models.Firewall.service_port, session=session).filter(
        models.Instance.id==models.Firewall.instance_id).filter(
            and_(models.Firewall.hostname==hostname,
                 models.Firewall.gateway_port==dst_port)).filter(
        models.Instance.host==models.Gateway.hostname)

    result = query.first()
    if result:
        instance_network = model_query(models.InstanceNetwork, session=session).\
                filter_by(instance_id=result.Instance.id).first()

        if not instance_network:
            return None

        result.Instance.address = instance_network['address']
        result.Instance.mac_address = instance_network['mac_address']

    return result
