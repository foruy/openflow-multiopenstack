import functools
import sys
import netaddr
import threading

from oslo_config import cfg
from oslo_db import options as oslo_db_options
from oslo_db.sqlalchemy import session as db_session
from oslo_db.sqlalchemy import utils as sqlalchemyutils
from oslo_log import log as logging
from oslo_utils import timeutils
from oslo_utils import uuidutils
from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload_all
from sqlalchemy.sql import func

from daoliproxy.db.sqlalchemy import models
from daoliproxy import exception
from daoliproxy.i18n import _, _LI, _LE, _LW

api_db_opts = [
    cfg.StrOpt('connection',
               help='The SQLAlchemy connection string to use to connect to '
                    'the Daoliproxy API database.',
               secret=True),
    cfg.BoolOpt('sqlite_synchronous',
                default=True,
                help='If True, SQLite uses synchronous mode.'),
    cfg.StrOpt('slave_connection',
               secret=True,
               help='The SQLAlchemy connection string to use to connect to the'
                    ' slave database.'),
    cfg.StrOpt('mysql_sql_mode',
               default='TRADITIONAL',
               help='The SQL mode to be used for MySQL sessions. '
                    'This option, including the default, overrides any '
                    'server-set SQL mode. To use whatever SQL mode '
                    'is set by the server configuration, '
                    'set this to no value. Example: mysql_sql_mode='),
    cfg.IntOpt('idle_timeout',
               default=3600,
               help='Timeout before idle SQL connections are reaped.'),
    cfg.IntOpt('max_pool_size',
               help='Maximum number of SQL connections to keep open in a '
                    'pool.'),
    cfg.IntOpt('max_retries',
               default=10,
               help='Maximum number of database connection retries '
                    'during startup. Set to -1 to specify an infinite '
                    'retry count.'),
    cfg.IntOpt('retry_interval',
               default=10,
               help='Interval between retries of opening a SQL connection.'),
    cfg.IntOpt('max_overflow',
               help='If set, use this value for max_overflow with '
                    'SQLAlchemy.'),
    cfg.IntOpt('connection_debug',
               default=0,
               help='Verbosity of SQL debugging information: 0=None, '
                    '100=Everything.'),
    cfg.BoolOpt('connection_trace',
                default=False,
                help='Add Python stack traces to SQL as comment strings.'),
    cfg.IntOpt('pool_timeout',
               help='If set, use this value for pool_timeout with '
                    'SQLAlchemy.'),
]

quota_opt = cfg.IntOpt('instance_count', default=10,
                       help="Default instance number for user")

CONF = cfg.CONF
CONF.register_opt(quota_opt)
CONF.register_opts(oslo_db_options.database_opts, 'database')
CONF.register_opts(api_db_opts, group='api_database')

LOG = logging.getLogger(__name__)

GATEWAY_MIN = 50000
GATEWAY_MAX = 65535

_ENGINE_FACADE = {'main': None, 'api': None}
_MAIN_FACADE = 'main'
_API_FACADE = 'api'
_LOCK = threading.Lock()


def _create_facade(conf_group):

    # NOTE(dheeraj): This fragment is copied from oslo.db
    return db_session.EngineFacade(
        sql_connection=conf_group.connection,
        slave_connection=conf_group.slave_connection,
        sqlite_fk=False,
        autocommit=True,
        expire_on_commit=False,
        mysql_sql_mode=conf_group.mysql_sql_mode,
        idle_timeout=conf_group.idle_timeout,
        connection_debug=conf_group.connection_debug,
        max_pool_size=conf_group.max_pool_size,
        max_overflow=conf_group.max_overflow,
        pool_timeout=conf_group.pool_timeout,
        sqlite_synchronous=conf_group.sqlite_synchronous,
        connection_trace=conf_group.connection_trace,
        max_retries=conf_group.max_retries,
        retry_interval=conf_group.retry_interval)

def _create_facade_lazily(facade, conf_group):
    global _LOCK, _ENGINE_FACADE
    if _ENGINE_FACADE[facade] is None:
        with _LOCK:
            if _ENGINE_FACADE[facade] is None:
                _ENGINE_FACADE[facade] = _create_facade(conf_group)
    return _ENGINE_FACADE[facade]


def get_engine(use_slave=False):
    conf_group = CONF.database
    facade = _create_facade_lazily(_MAIN_FACADE, conf_group)
    return facade.get_engine(use_slave=use_slave)


def get_api_engine():
    conf_group = CONF.api_database
    facade = _create_facade_lazily(_API_FACADE, conf_group)
    return facade.get_engine()


def get_session(use_slave=False, **kwargs):
    conf_group = CONF.database
    facade = _create_facade_lazily(_MAIN_FACADE, conf_group)
    return facade.get_session(use_slave=use_slave, **kwargs)

def get_api_session(**kwargs):
    conf_group = CONF.api_database
    facade = _create_facade_lazily(_API_FACADE, conf_group)
    return facade.get_session(**kwargs)


def get_backend():
    """The backend is this module itself."""
    return sys.modules[__name__]


def require_admin_context(f):
    """Decorator to require admin request context.

    The first argument to the wrapped function must be the context.

    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        nova.context.require_admin_context(args[0])
        return f(*args, **kwargs)
    return wrapper

def require_context(f):
    """Decorator to require *any* user or admin context.

    This does no authorization for user or project access matching, see
    :py:func:`nova.context.authorize_project_context` and
    :py:func:`nova.context.authorize_user_context`.

    The first argument to the wrapped function must be the context.

    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        nova.context.require_context(args[0])
        return f(*args, **kwargs)
    return wrapper

def _retry_on_deadlock(f):
    """Decorator to retry a DB API call if Deadlock was received."""
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        while True:
            try:
                return f(*args, **kwargs)
            except db_exc.DBDeadlock:
                LOG.warning(_LW("Deadlock detected when running "
                                "'%(func_name)s': Retrying..."),
                            dict(func_name=f.__name__))
                # Retry!
                time.sleep(0.5)
                continue
    functools.update_wrapper(wrapped, f)
    return wrapped


def model_query(context, model,
                args=None,
                session=None,
                use_slave=False,
                read_deleted="yes",
                project_only=False):
    """Query helper that accounts for context's `read_deleted` field.

    :param context:     NovaContext of the query.
    :param model:       Model to query. Must be a subclass of ModelBase.
    :param args:        Arguments to query. If None - model is used.
    :param session:     If present, the session to use.
    :param use_slave:   If true, use a slave connection to the DB if creating a
                        session.
    :param read_deleted: If not None, overrides context's read_deleted field.
                        Permitted values are 'no', which does not return
                        deleted values; 'only', which only returns deleted
                        values; and 'yes', which does not filter deleted
                        values.
    :param project_only: If set and context is user-type, then restrict
                        query to match the context's project_id. If set to
                        'allow_none', restriction includes project_id = None.
    """

    if session is None:
        if CONF.database.slave_connection == '':
            use_slave = False
        session = get_session(use_slave=use_slave)

    if read_deleted is None:
        read_deleted = context.read_deleted

    query_kwargs = {}
    if 'no' == read_deleted:
        query_kwargs['deleted'] = False
    elif 'only' == read_deleted:
        query_kwargs['deleted'] = True
    elif 'yes' == read_deleted:
        pass
    else:
        raise ValueError(_("Unrecognized read_deleted value '%s'")
                           % read_deleted)

    query = sqlalchemyutils.model_query(model, session, args, **query_kwargs)

    return query

#############

def authenticate(context, username, password, **kwargs):
    session = get_session()
    with session.begin():
        user = model_query(context, models.User, session=session).filter_by(
                username=username, password=password).first()

        if user:
            user['updated_at'] = timeutils.utcnow()
            user_login = models.UserLogin()
            user_login.user_id = user.id
            user_login.updated_at = timeutils.utcnow()
            user_login.update(kwargs)
            user_login.save(session=session)
        else:
            raise exception.UserNotFound(user=username)

    return user

def user_token_create(context, user_id, token=None):
    if token is None:
        token = uuidutils.generate_uuid()

    token_ref = models.UserToken()
    token_ref.id = token
    token_ref.user_id = user_id
    token_ref.save()

    return token_ref

def keystone_token_create(context, **values):
    token_ref = models.KeystoneToken()
    token_ref.update(values)
    token_ref.save()

    return token_ref

def user_token_get(context, token):
    result = model_query(context, models.UserToken).filter_by(
             id=token).first()

    if not result:
        raise exception.TokenNotFound(token=token)

    return result

def keystone_token_get(context, token):
    return model_query(context, models.KeystoneToken).filter_by(
            user_token_id=token).all()

def user_absolute_limits(context, user_id, zone_id=None):
    session = get_session()

    user_ref = user_get(context, user_id, session=session)

    query = model_query(context, models.Instance,
            (func.count(models.Instance.id),),
            session=session).filter_by(user_id=user_id)

    if zone_id is not None:
        query = query.filter_by(zone_id=zone_id)

    quotas = query.with_lockmode('update').first()

    max_instances = user_ref.get('default_instances', CONF.instance_count)

    used_instances = quotas[0] if quotas else max_instances

    return {"maxTotalInstances": max_instances,
            "totalInstancesUsed": used_instances}


def zone_get(context, id):
    return model_query(context, models.Zone).filter_by(id=id).first()

def zone_get_all(context, idc_id=None, disabled=True):
    query = model_query(context, models.Zone)

    if idc_id is not None:
        query = query.filter_by(idc_id=idc_id)

    if not disabled:
        query = query.filter_by(disabled=False)

    return query.all()

def zone_create(context, values):
    session = get_session()
    zone = models.Zone()
    zone.update(values)
    zone.save(session=session)
    return zone

def zone_delete(context, id):
    model_query(context, models.Zone).filter_by(id=id).delete()

def zone_update(context, id, values):
    session = get_session()

    zone = model_query(context, models.Zone, session=session).filter_by(
            id=id).first()

    if not zone:
        # zone may be empty when administrator deleted
        return

    zone.update(values)
    zone.save(session=session)

    return zone

def zone_exists(context, auth_url=None):
    query = model_query(context, models.Zone)
    query = query.filter_by(auth_url=auth_url)
    return query.first()

def zone_get_by_image(context, image_id, zones):
    session = get_session()
    zone_ref = []

    image_ref = model_query(context, models.Image, (models.Image.name,),
            session=session).filter_by(imageid=image_id).first()

    if image_ref is not None:
        zone_ref = model_query(context, models.Zone, (models.Zone.id,
            models.Image.imageid), session=session).filter(
            models.Zone.id==models.Image.zone_id).filter(
                models.Zone.id.in_(zones)).filter(
                models.Image.name==image_ref.name).filter_by(
                disabled=False).all()

        status = model_query(context, models.Instance,
                (models.Instance.zone_id, func.count(
                models.Instance.id)), session=session).filter(
                models.Instance.zone_id.in_(
                [z[0] for z in zone_ref])).group_by(
                models.Instance.zone_id).all()

        status_dict = dict((s[0],s[1]) for s in status)

    return dict((z[0], [status_dict.get(z[0], 0),
                 z[1]]) for z in zone_ref)

def user_get(context, id, session=None):
    session = session or get_session()

    result = model_query(context, models.User,
            session=session).filter_by(id=id).first()

    if not result:
        raise exception.UserNotFound(user=user_id)

    return result

def user_get_all(context):
    return model_query(context, models.User).all()

def service_get_by_idc(context, idc_id):
    return model_query(context, models.Service).filter_by(
            idc_id=idc_id).all()

def service_create(context, values):
    session = get_session()

    with session.begin():
        service_ref = model_query(context, models.Service,
                              session=session).filter_by(
                name=values['name']).first()

        if service_ref:
            service_ref.update(values)
        else:
            service_ref = models.Service()
            service_ref.update(values)
            service_ref.save(session=session)

        return service_ref

def server_get_all(context, user_id=None):
    query = model_query(context, models.Instance)

    if user_id is not None:
        query = query.filter_by(user_id=user_id)

    query = query.options(joinedload_all('addresses.addresses'))
    query = query.order_by(models.Instance.created_at.desc())

    return query.all()

def user_delete(context, id):
    session = get_session()

    with session.begin():
        model_query(context, models.SingleSecurityGroup,
                session=session).filter_by(user_id=id).delete()
        model_query(context, models.UserLogin,
                session=session).filter_by(user_id=id).delete()
        model_query(context, models.Subnet,
                session=session).filter_by(user_id=id).delete()
        model_query(context, models.User, session=session).filter_by(
                id=id).delete()

def user_check(context, key, val):
    query = model_query(context, models.User)

    if key == 'username':
        query = query.filter_by(username=val)
    elif key == 'email':
        query = query.filter_by(email=val)
    elif key == 'phone':
        query = query.filter_by(phone=val)
    else:
        raise Exception("Invalid key")

    return query.first()

def register(context, **values):
    session = get_session()
    user_ref = models.User()
    user_ref.update(values)
    user_ref.save(session=session)
    return user_ref

def user_task(context, utype, uobj):
    session = get_session()
    user_task_ref = models.UserTask()
    user_task_ref.utype = utype
    user_task_ref.uobj = uobj
    user_task_ref.save(session=session)
    return user_task_ref

def validate_user(context, user, session=None):
    session = session or get_session()
    query = model_query(context, models.User, session=session)

    for k, v in user.items():
        if isinstance(v, unicode):
            v = '"%s"' % v
        query = query.filter('%s=%s' % (k, v))

    return query.first()

def update_user(context, base, **values):
    session = get_session()

    with session.begin():
        user_ref = validate_user(context, base, session=session)

        if not user_ref:
            raise exception.UserNotFound(user=base['username'])

        user_ref.update(values)

        return user_ref

def user_login_list(context, user_id=None):
    query = model_query(context, models.UserLogin)

    if user_id is not None:
        query = query.filter_by(user_id=user_id)

    query = query.order_by(models.UserLogin.updated_at.desc())

    return query.all()


def server_get(context, id, session=None):
    session = session or get_session()

    server_ref = model_query(context, models.Instance,
            session=session).options(joinedload_all(
            'addresses.addresses')).filter_by(
            id=id).first()

    if not server_ref:
        raise exception.InstanceNotFound(id=id)

    return server_ref

def server_get_by_zone(context, zone_id):
    return model_query(context, models.Instance).filter_by(
        zone_id=zone_id).all()

def address_filter(context, user_id, address):
    return model_query(context, models.InstanceNetwork).filter(
        models.Instance.id==models.InstanceNetwork.instance_id).filter(
        models.Instance.user_id==user_id).filter_by(
        address=address).with_lockmode('update').first()

def server_create(context, values):
    session = get_session()

    instance_ref = models.Instance()
    instance_ref.update(values)
    instance_ref.save(session=session)

    return instance_ref

def server_delete(context, id):
    session = get_session()

    with session.begin():
        model_query(context, models.Instance,
            session=session).filter_by(id=id).delete()
        model_query(context, models.SingleSecurityGroup,
            session=session).filter(or_(
                models.SingleSecurityGroup.start==id,
                models.SingleSecurityGroup.end==id,
            )).delete()
        model_query(context, models.Firewall,
            session=session).filter_by(instance_id=id).delete()

def server_update(context, id, values):
    session = get_session()
    addresses = values.pop('addresses', [])

    query = model_query(context, models.Instance, session=session)
    server_ref = query.filter_by(id=id).first()

    if not server_ref:
        raise exception.InstanceNotFound(id=id)

    server_ref.update(values)
    server_ref.save(session=session)

    for address in addresses:
        instance_network = models.InstanceNetwork()
        instance_network.instance_id = id
        instance_network.update(address)
        instance_network.save(session=session)

    return server_ref

def role_get_by_name(context, user_id):
    result = model_query(context, models.User).filter_by(
        id=user_id, username='admin').first()

    if not result:
        raise exception.AdminRequired(user=user_id)

    return result

def image_get_all(context, zone_id=None):
    query = model_query(context, models.Image)

    if zone_id is not None:
        query = query.filter_by(zone_id=zone_id)

    return query.all()

def image_get(context, image_id):
    return model_query(context, models.Image).filter_by(
            imageid=image_id).first()

def image_delete(context, id=None, zone_id=None):
    query = model_query(context, models.Image)

    if id is not None:
        query = query.filter_by(id=id)
    elif zone_id is not None:
        query = query.filter_by(zone_id=zone_id)

    query.delete()

def image_create(context, zone_id, values):
    session = get_session()
    image = models.Image()
    image.zone_id = zone_id
    image.update(values)
    image.save(session=session)
    return image


def flavor_get_all(context, zone_id=None):
    query = model_query(context, models.Flavor)

    if zone_id is not None:
        query = query.filter_by(zone_id=zone_id)

    return query.all()

def flavor_get(context, id, zone_id=None):
    query = model_query(context, models.Flavor).filter_by(flavorid=id)

    if zone_id is not None:
        query = query.filter_by(zone_id=zone_id)

    return query.first()

def flavor_delete(context, id=None, zone_id=None):
    query = model_query(context, models.Flavor)

    if id is not None:
        query = query.filter_by(id=id)
    elif zone_id is not None:
        query = query.filter_by(zone_id=zone_id)

    query.delete()

def flavor_create(context, zone_id, values):
    session = get_session()
    flavor = models.Flavor()
    flavor.zone_id = zone_id
    flavor.update(values)
    flavor.save(session=session)
    return flavor


def gateway_get_all(context, zone_id=None):
    query = model_query(context, models.Gateway)

    if zone_id is not None:
        query = query.filter_by(zone_id=zone_id)

    return query.all()

def gateway_get(context, hostname):
    return model_query(context, models.Gateway).filter_by(
            hostname=hostname).first()

def gateway_delete(context, id=None, zone_id=None):
    query = model_query(context, models.Gateway)

    if id is not None:
        query = query.filter_by(id=id)
    elif zone_id is not None:
        query = query.filter_by(zone_id=zone_id)

    query.delete()

def gateway_update(context, hostname, values):
    session = get_session()
    gateway = model_query(context, models.Gateway,
                          session=session).filter_by(
            hostname=hostname).first()

    with session.begin():
        gateway.update(values)

    return gateway

def gateway_create(context, zone_id, values):
    session = get_session()
    gateway = models.Gateway()
    gateway.zone_id = zone_id
    gateway.update(values)
    gateway.save(session=session)
    return gateway

def gateway_count(context, hostname):
    session = get_session()
    with session.begin():
        gateway = model_query(context, models.Gateway,
                session=session).filter_by(
                hostname=hostname).with_lockmode('update').first()

        if gateway.count < GATEWAY_MIN:
            gateway.count = GATEWAY_MIN
        elif gateway.count >= GATEWAY_MAX:
            gateway.count = GATEWAY_MIN
        else:
            gateway.count += 1

    return gateway

def gateway_get_by_idc(context, idc_id):
    query = model_query(context, models.Gateway).filter_by(idc_id=idc_id)

    _query = query.filter(or_(
                models.Gateway.vext_ip!=models.Gateway.ext_ip,
                models.Gateway.int_dev!=models.Gateway.ext_dev))

    result = _query.filter_by(disabled=False).all()

    if not result:
        result = query.all()

    return result


def network_get(context, net_id=None, zone_id=None):
    query = model_query(context, models.Network,
            (models.Network.networkid, models.NetworkType.cidr)).filter(
            models.Network.netype==models.NetworkType.id)

    if net_id is not None:
        query = query.filter(models.Network.netype==net_id)

    if zone_id is not None:
        query = query.filter(models.Network.zone_id==zone_id)

    result = query.first()

    if not result:
        raise exception.NetworkTypeNotFound(id=net_id or zone_id)

    return result

def network_get_all(context, zone_id=None):
    query = model_query(context, models.Network)

    if zone_id is not None:
        query = query.filter_by(zone_id=zone_id)

    return query.all()

def network_delete(context, id=None, zone_id=None):
    query = model_query(context, models.Network)

    if id is not None:
        query = query.filter_by(id=id)
    elif zone_id is not None:
        query = query.filter_by(zone_id=zone_id)

    query.delete()

def network_create(context, zone_id, values):
    session = get_session()
    network = models.Network()
    network.zone_id = zone_id
    network.update(values)
    network.save(session=session)
    return network

def network_type_get(context, id):
    query = model_query(context, models.NetworkType)

    result = query.filter_by(id=id).first()

    if not result:
        raise exception.NetworkTypeNotFound(id=id)

    return result

def network_type_list(context):
    return model_query(context, models.NetworkType).all()

def network_type_update(context, cidr):
    session = get_session()

    with session.begin():
        network_type = model_query(context, models.NetworkType,
                session=session).filter_by(cidr=cidr).first()

        if not network_type:
            network_type = models.NetworkType()
            network_type.cidr = cidr
            network_type.save(session=session)

    return network_type

def network_type_delete(context, id):
    model_query(context, models.NetworkType).filter_by(id=id).delete()

def create_subnet(context, user_id, netype, subnet=None, session=None):
    session = session or get_session()

    if subnet is None:
        subnet = {'cidr': network_type_get(context, netype).cidr}

    net = netaddr.IPNetwork(subnet['cidr'])

    if not subnet.has_key('gateway_ip') or subnet['gateway_ip'] is None:
        subnet['gateway_ip'] = str(netaddr.IPAddress(net.last - 1))

    pool = {'start': str(netaddr.IPAddress(net.first + 2)),
            'end': str(netaddr.IPAddress(net.last - 2))}

    with session.begin():
        args = {'id': subnet.get('id') or uuidutils.generate_uuid(),
                'name': subnet.get('name', ''),
                'cidr': subnet['cidr'],
                'gateway_ip': subnet['gateway_ip'],
                'netype': netype,
                'user_id': user_id}
        subnet = models.Subnet(**args)
        session.add(subnet)

        ip_pool = models.IPAllocationPool(subnet=subnet,
                                          first_ip=pool['start'],
                                          last_ip=pool['end'])
        session.add(ip_pool)
        ip_range = models.IPAvailabilityRange(
                ipallocationpool=ip_pool,
                first_ip=pool['start'],
                last_ip=pool['end'])
        session.add(ip_range)

    return subnet

def generate_ip(context, user_id, netype):
    """Generate an IP address."""
    session = get_session()
    subnet = model_query(context, models.Subnet, session=session).filter_by(
        user_id=user_id, netype=netype).first()

    if not subnet:
        create_subnet(context, user_id, netype, session=session)

    query = model_query(context, models.IPAvailabilityRange,
            session=session).join(models.IPAllocationPool).join(
            models.Subnet).with_lockmode('update')

    range = query.filter_by(user_id=user_id, netype=netype).first()

    if not range:
        LOG.debug(_("All IPs allocated"))
        return

    ip_address = range['first_ip']
    with session.begin():
        LOG.debug(_("Allocated IP - %(ip_address)s from %(first_ip)s "
                   "to %(last_ip)s"),
                  {'ip_address': ip_address,
                   'first_ip': range['first_ip'],
                   'last_ip': range['last_ip']})
        if range['first_ip'] == range['last_ip']:
            session.delete(range)
        else:
            # increment the first free
            range['first_ip'] = str(netaddr.IPAddress(ip_address) + 1)

    return ip_address


def security_group_get(context, user_id):
    return model_query(context, models.SingleSecurityGroup).filter_by(
            user_id=user_id).all()

def security_group_list(context):
    return model_query(context, models.SingleSecurityGroup).all()

def security_group_create(context, user_id, start, end):
    session = get_session()
    group_ref = models.SingleSecurityGroup()
    group_ref.start = start
    group_ref.end = end
    group_ref.user_id = user_id
    group_ref.save(session=session)
    return group_ref

def security_group_delete(context, user_id, start, end):
    session = get_session()

    with session.begin():
        query = model_query(context, models.SingleSecurityGroup,
                            session=session).filter_by(user_id=user_id)

        query = query.filter(or_(
                and_(models.SingleSecurityGroup.start==start,
                         models.SingleSecurityGroup.end==end),
                and_(models.SingleSecurityGroup.start==end,
                         models.SingleSecurityGroup.end==start)))

        query.delete()

def firewall_get(context, id=None, hostname=None, gateway_port=None):
    query = model_query(context, models.Firewall)
    if id is not None:
        query = query.filter_by(id=id)
    if hostname is not None:
        query = query.filter_by(hostname=hostname)
    if gateway_port is not None:
        query = query.filter_by(gateway_port=gateway_port)

    return query.first()

def firewall_get_by_instance(context, instance_id):
    return model_query(context, models.Firewall).filter_by(
            instance_id=instance_id).all()

def firewall_create(context, values):
    session = get_session()
    firewall_ref = models.Firewall()
    firewall_ref.update(values)
    firewall_ref.save(session=session)
    return firewall_ref

def firewall_delete(context, id):
    model_query(context, models.Firewall).filter_by(
            id=id).delete()

def resource_get(context, user_id=None, source_id=None, source_name=None):
    query = model_query(context, models.Resource)

    if user_id:
        query = query.filter_by(user_id=user_id)

    if source_id:
        query = query.filter_by(source_id=source_id)

    if source_name:
        query = query.filter_by(source_name=source_name)

    return query.all()

def resource_create(context, source_name, source_id, action, user_id,
                    extra=None):
    session = get_session()

    if extra is None:
        extra = {}

    resource = models.Resource()
    resource.source_name = source_name
    resource.source_id = source_id
    resource.action = action
    resource.extra = extra
    resource.user_id = user_id
    resource.save(session=session)

    return resource
