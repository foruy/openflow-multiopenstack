import webob
from webob import exc
from eventlet import greenthread

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import timeutils

from daoliproxy import agent
from daoliproxy.api.base import BaseController
from daoliproxy.api import common
from daoliproxy.api.openstack import wsgi
from daoliproxy.api import power_state
from daoliproxy.api import vm_states
from daoliproxy import exception
from daoliproxy.i18n import _

instance_opts = [
    cfg.IntOpt('instance_try', default=200,
               help='Instance retry count'),
    cfg.IntOpt('instance_interval', default=30,
               help='Instance interval gap')
]

CONF = cfg.CONF
CONF.register_opts(instance_opts)

LOG = logging.getLogger(__name__)

class Controller(BaseController):
    """The zone API controller.
    """

    def list(self, req):
        context = req.environ['proxy.context']
        return {"servers": self._get_servers(context, context.user_id)}

    def detail(self, req):
        context = req.environ['proxy.context']

        try:
            self.db.role_get_by_name(context, context.user_id)
        except exception.AdminRequired as e:
            raise exc.HTTPForbidden(explanation=e)

        return {"servers": self._get_servers(context)}

    def _get_servers(self, context, user_id=None):
        novail_zones = [zone.id for zone in self.db.zone_get_all(context)
                        if zone['disabled']]
        servers = []

        for server in self.db.server_get_all(context, user_id=user_id):
            if server['zone_id'] in novail_zones:
                server['status'] = None

            server['status'] = common.status_from_state(server['status'])
            #server['addresses'] = self._format_address(server['addresses'])
            servers.append(server)

        return servers

    def get(self, req, id):
        context = req.environ['proxy.context']

        try:
            server = self.db.server_get(context, id)
        except exception.InstanceNotFound:
            msg = _("Instance not found")
            raise exc.HTTPNotFound(explanation=msg)

        server['status'] = common.status_from_state(server['status'])

        return {'server': server}

    def available_gateway(self, context, hostname):
        gateway = self.db.gateway_get(context, hostname)

        avail_gateway = [g.hostname for g in self.db.gateway_get_by_idc(
                         context, gateway.idc_id)]

        if avail_gateway and hostname not in avail_gateway:
            return avail_gateway[0]

        return hostname

    def _format_address(self, addresses):
        _addresses = []

        for addr in addresses:
            _address = {}
            _address['address'] = addr.address
            _address['mac_address'] = addr.mac_address
            _address['network_id'] = addr.network_id
            _address['id'] = addr.id
            _address['instance_id'] = addr.instance_id
            _address['version'] = addr.version
            _addresses.append(_address)

        return _addresses

    def _format_server(self, server, **kwargs):
        _server = {}
        _server["id"] = server.id

        nics = kwargs.get('nics', [])
        nics_dict = dict((n['v4-fixed-ip'], n['net-id']) for n in nics)

        addresses = []
        if server.addresses.values():
            for net in server.addresses.values()[0]:
                addr = {}
                addr['address'] = net['addr']
                addr['mac_address'] = net.get('OS-EXT-IPS-MAC:mac_addr')
                addr['network_id'] = nics_dict.get(net['addr'])
                addr['version'] = net['version']
                addresses.append(addr)
 
        _server["addresses"] = addresses

        try:
            _server["host"] = getattr(server, 'OS-EXT-SRV-ATTR:host')
        except:
            _server["host"] = server.host

        _server["fake_hostname"] = _server["host"]
        _server["status"] = server.status.lower()
        _server["keystone_project_id"] = server.tenant_id
        _server["power_state"] = getattr(server, 'OS-EXT-STS:power_state')
        _server["created_at"] = timeutils.strtime(
                timeutils.parse_isotime(server.created))

        _server.update(kwargs)

        return _server

    def _server_update_thread(self, context, id, zone, image, flavor,
            gateway_name=None, device_mapping=None, nics=None):
        try_count = CONF.instance_try

        while try_count > 0:
            try_count -= 1
            server = agent.server_get(self.request_get(context, zone), id)

            if server and server.status.lower() in (vm_states.ACTIVE, vm_states.ERROR):
                _server = self._format_server(server, nics=nics)
                if server.status.lower() == vm_states.ACTIVE:
                    image_obj = self.db.image_get(context, image)

                    if gateway_name is None:
                        gateway_name = self.available_gateway(context, _server['host'])

                    firewall = {'instance_id': id, 'hostname': gateway_name}

                    for port in image_obj.get('property', []):
                        gateway = self.db.gateway_count(context, gateway_name)
                        firewall['gateway_port'] = gateway.count
                        firewall['service_port'] = port
                        self._firewall_create(context, firewall)

                    self.resource_notify(context, 'instance.create', id,
                            zone=zone, flavor=flavor)

                    if device_mapping is not None:
                        self.resource_notify(context, 'disk.create', id,
                            device_mapping=device_mapping)

                self.db.server_update(context, id, _server)
                break
            else:
                greenthread.sleep(2)

    def simple_scheduler(self, context, avail_zones, **kwargs):
        while len(avail_zones) > 0:
            avail_zone = min(avail_zones.iteritems(), key=lambda d:d[1][0])
            zone_id = avail_zone[0]
            image_id = avail_zone[1][1]
            avail_zones[zone_id][0] += 1

            if zone_id not in context.service_catalog.keys():
                avail_zones.pop(zone_id)
                continue

            limit = self.db.user_absolute_limits(context, context.user_id)

            if (limit['maxTotalInstances'] - limit['totalInstancesUsed']
                                           - kwargs['instance_count'] < 0):
                avail_zones.pop(zone_id)
                continue

            return (zone_id, image_id)

    def create(self, req, body):
        all_servers = []
        server = self._from_body(body, 'server')
        kwargs = self._from_body(body, 'kwargs')
        context = req.environ['proxy.context']

        netype = int(kwargs.pop('netype', 1))
        count = int(kwargs['instance_count'])
        image_id = server.pop('image', None)
        device_mapping = kwargs.get('block_device_mapping_v2')

        if image_id is None and device_mapping:
            for device in device_mapping:
                if device['source_type'] == 'image':
                    image_id = device['uuid']
                    break

        if image_id is None:
            msg = _("You must select an image.")
            raise exc.HTTPBadRequest(explanation=msg)

        gateway_name = kwargs.pop('gateway', None)

        if gateway_name and not self.db.gateway_get(context, gateway_name):
            msg = _("Gateway name %s could not be found") % gateway_name
            raise exc.HTTPNotFound(explanation=msg)

        msg = _("Availiable zone not found")
        zone_id = kwargs.pop('zone_id', None)

        if zone_id is None:
            avail_zones = self.db.zone_get_by_image(
                    context, image_id, context.service_catalog.keys())
            if not avail_zones:
                raise exc.HTTPNotFound(explanation=msg)
        else:
            if not self.db.zone_get(context, zone_id) or \
                    zone_id not in context.service_catalog.keys():
                raise exc.HTTPNotFound(explanation=msg)

            avail_zones = self.db.zone_get_by_image(context, image_id, [zone_id])

        for i in range(count):
            kwargs.pop('accessIPv4', None)
            kwargs['instance_count'] = 1

            resource = self.simple_scheduler(context, avail_zones, **kwargs)
            if not resource:
                msg = _("Quota exceeded.")
                raise exc.HTTPBadRequest(explanation=msg)

            LOG.info("Selected zone %s", resource)
            zone_id, image_id = resource

            try:
                network = self.db.network_get(context, net_id=netype, zone_id=zone_id)
                while True:
                    ip_address = self.db.generate_ip(context, context.user_id, netype)
                    if not ip_address:
                        msg = _("All IPs allocated")
                        raise exc.HTTPConflict(explanation=msg)

                    if not self.db.address_filter(context, context.user_id, ip_address):
                        break

                kwargs['nics'] = [{'net-id': network.networkid, 'v4-fixed-ip': ip_address}]
            except exception.NetworkTypeNotFound as e:
                raise exc.HTTPNotFound(explanation=e.args[0])

            if count > 1:
                name = '%s-%s' % (server['name'], ip_address.replace('.', '-'))
            else:
                name = server['name']

            zone = self.db.zone_get(context, zone_id)

            if zone.idc_id != CONF.idc_id:
                base = {'name': name,
                        'image_id': image_id,
                        'zone_id': zone_id,
                        'gateway_name': gateway_name}

                _server = self.proxy_method('server_create_proxy', context,
                        zone.idc_id, base, server, kwargs).to_dict()
            else:
                inst = agent.server_create(self.request_get(context, zone_id),
                        server['name'], image_id, server['flavor'], **kwargs)

                _server = {'id': inst.id,
                           'name': name,
                           'zone_id': zone_id,
                           'user_id': context.user_id,
                           'image_id': image_id,
                           'flavor_id': server['flavor'],
                           'status': vm_states.BUILDING,
                           'updated_at': timeutils.utcnow(),
                }
                self.db.server_create(context, _server)

                self.add_thread(self._server_update_thread,
                                context, inst.id,
                                zone_id,
                                image_id,
                                server['flavor'],
                                gateway_name,
                                device_mapping,
                                kwargs['nics'])

            all_servers.append(_server)

        return {'server': {'servers': all_servers}}

    def create_proxy(self, req, body):
        base = self._from_body(body, 'base')
        server = self._from_body(body, 'server')
        kwargs = self._from_body(body, 'kwargs')
        context = req.environ['proxy.context']

        inst = agent.server_create(self.request_get(context,
                base['zone_id']), server['name'],
                base['image_id'], server['flavor'], **kwargs)

        _server = {'id': inst.id,
                   'name': base['name'],
                   'zone_id': base['zone_id'],
                   'user_id': context.user_id,
                   #'address': kwargs['nics'][0]['v4-fixed-ip'],
                   'image_id': base['image_id'],
                   'flavor_id': server['flavor'],
                   'status': vm_states.BUILDING,
                   'updated_at': timeutils.utcnow(),
        }
        self.db.server_create(context, _server)

        self.add_thread(self._server_update_thread,
                        context, inst.id,
                        base['zone_id'],
                        base['image_id'],
                        server['flavor'],
                        base['gateway_name'],
                        kwargs.get('block_device_mapping_v2'),
                        kwargs['nics'])

        return {'server': _server}

    def delete(self, req, id):
        self._delete(req, id)

    def delete_proxy(self, req, id):
         self._delete(req, id, checked=False)

    def _delete(self, req, id, checked=False):
        context = req.environ['proxy.context']

        try:
            server = self.db.server_get(context, id)
        except exception.InstanceNotFound:
            msg = _("Instance not found")
            raise exc.HTTPNotFound(explanation=msg)

        zone = self.db.zone_get(context, server.zone_id)

        if zone:
            if checked and zone.idc_id != CONF.idc_id:
                return self.proxy_method('server_delete_proxy',
                                         context, zone.idc_id, id)

            try:
                agent.server_delete(self.request_get(
                        context, server.zone_id), id)
            except exception.novaclient.Unauthorized as e:
                raise exc.HTTPUnauthorized(e)
            except exception.novaclient.NotFound as e:
                LOG.error(e)

        self.resource_notify(context, 'instance.delete', id)
        self.resource_notify(context, 'disk.delete', id)
        self.db.server_delete(context, id)

    @wsgi.action('os-start')
    def start_server(self, req, id, body):
        self._server_action('start', req, id)
        return webob.Response(status_int=202)

    @wsgi.action('os-start-proxy')
    def start_server_proxy(self, req, id, body):
        self._server_action('start', req, id, checked=False)

    @wsgi.action('os-stop')
    def stop_server(self, req, id, body):
        self._server_action('stop', req, id)
        return webob.Response(status_int=202)

    @wsgi.action('os-stop-proxy')
    def stop_server_proxy(self, req, id, body):
        self._server_action('stop', req, id, checked=False)

    def _server_action(self, action, req, id, checked=False):
        context = req.environ['proxy.context']
        server = self.db.server_get(context, id)

        if checked:
            zone = self.db.zone_get(context, server.zone_id)
            if zone.idc_id != CONF.idc_id:
                return self.proxy_method('server_%s_proxy' % action,
                                         context, zone.idc_id, id)

        status = {'updated_at': timeutils.utcnow()}

        if not timeutils.is_older_than(
                server['updated_at'], CONF.instance_interval):
            msg = _("Your operation is too frequent. Please try again later.")
            raise exc.HTTPLocked(explanation=msg)

        if action == 'start':
            status['status'] = vm_states.ACTIVE
            status['power_state'] = power_state.RUNNING
        elif action == 'stop':
            func = agent.server_stop
            status['status'] = vm_states.STOPPED
            status['power_state'] = power_state.SHUTDOWN
        else:
            msg = _('Action "%s" do not supported') % action
            raise HTTPBadRequest(explanation=msg)

        try:
            getattr(agent, 'server_%s' % action)(self.request_get(
                    context, server.zone_id), id)
        except exception.novaclient.Conflict as e:
            LOG.error(e)

        self.db.server_update(context, id, status)
        self.resource_notify(context, 'instance.%s' % action, id)

    def resource_notify(self, context, event, id, zone=None, **kwargs):
        if '.' not in event:
            LOG.error("Event %s error", event)
            return

        if kwargs.has_key('flavor'):
            kwargs['flavor'] = self.db.flavor_get(context, kwargs['flavor'],
                                                  zone_id=zone)
        name, _, action = event.partition('.')
        self.db.resource_create(context, name, id, action,
                                context.user_id, extra=kwargs)

    @wsgi.action('os-monitor')
    def monitor(self, req, id, body):
        return {'monitor': {'url': '/'}}

def create_resource():
    return wsgi.Resource(Controller())
