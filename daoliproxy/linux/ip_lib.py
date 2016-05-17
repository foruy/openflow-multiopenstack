import os
import sys

import netifaces as nis
from netaddr import IPNetwork

from daoliproxy import utils

NIC_PREFIX = ['et', 'em', 'en']

class SubProcessBase(object):
    def __init__(self, namespace=None,
                 log_fail_as_error=True):
        self.namespace = namespace
        self.log_fail_as_error = log_fail_as_error
        self.force_root = False

    def _run(self, options, command, args):
        if self.namespace:
            return self._as_root(options, command, args)
        elif self.force_root:
            return self._execute(options, command, args, run_as_root=True,
                                 log_fail_as_error=self.log_fail_as_error)
        else:
            return self._execute(options, command, args,
                                 log_fail_as_error=self.log_fail_as_error)

    def _as_root(self, options, command, args, use_root_namespace=False):
        namespace = self.namespace if not use_root_namespace else None

        return self._execute(options, command, args, run_as_root=True,
                             namespace=namespace,
                             log_fail_as_error=log_fail_as_error)

    @classmethod
    def _execute(cls, options, command, args, run_as_root=False,
                 namespace=None, log_fail_as_error=True):
        opt_list = ['-%s' % o for o in options]
        ip_cmd = add_namespace_to_cmd(['ip'], namespace)
        cmd = ip_cmd + opt_list + [command] + list(args)
        return utils.execute(*cmd, run_as_root=run_as_root)[0]

class IPDevice(SubProcessBase):
    def __init__(self, name, namespace=None):
        super(IPDevice, self).__init__(namespace=namespace)
        self.name = name
        self.link = IpLinkCommand(self)
        self.addr = IpAddrCommand(self)
        self.route = IpRouteCommand(self)

    def __eq__(self, other):
        return (other is not None and self.name == other.name
                and self.namespace == other.namespace)

    def __str__(self):
        return self.name

class IpCommandBase(object):
    COMMAND = ''

    def __init__(self, parent):
        self._parent = parent

    def _run(self, options, args):
        return self._parent._run(options, self.COMMAND, args)

    def _as_root(self, options, args, use_root_namespace=False):
        return self._parent._as_root(options,
                                     self.COMMAND,
                                     args,
                                     use_root_namespace=use_root_namespace)

class IpDeviceCommandBase(IpCommandBase):
    @property
    def name(self):
        return self._parent.name

class IpLinkCommand(IpDeviceCommandBase):
    COMMAND = 'link'

    def set_address(self, mac_address):
        self._as_root([], ('set', self.name, 'address', mac_address))

    @property
    def address(self):
        return self.attributes.get('link/ether')

    @property
    def state(self):
        return self.attributes.get('state')

    @property
    def attributes(self):
        return self._parse_line(self._run(['o'], ('show', self.name)))

    def _parse_line(self, value):
        if not value:
            return {}

        device_name, settings = value.replace("\\", '').split('>', 1)
        tokens = settings.split()
        keys = tokens[::2]
        values = [int(v) if v.isdigit() else v for v in tokens[1::2]]

        retval = dict(zip(keys, values))
        return retval

class IpAddrCommand(IpDeviceCommandBase):
    COMMAND = 'addr'

    def list(self, scope=None, to=None, filters=None, ip_version=None):
        options = [ip_version] if ip_version else []
        args = ['show', self.name]
        if filters:
            args += filters

        retval = []

        if scope:
            args += ['scope', scope]
        if to:
            args += ['to', to]

        for line in self._run(options, tuple(args)).split('\n'):
            line = line.strip()
            if not line.startswith('inet'):
                continue
            parts = line.split()
            if parts[0] == 'inet6':
                scope = parts[3]
            else:
                if parts[2] == 'brd':
                    scope = parts[5]
                else:
                    scope = parts[3]

            retval.append(dict(cidr=parts[1],
                               scope=scope,
                               dynamic=('dynamic' == parts[-1])))
        return retval

class IpRouteCommand(IpDeviceCommandBase):
    COMMAND = 'route'

    def get_gateway(self, scope=None, filters=None, ip_version=None):
        options = [ip_version] if ip_version else []

        args = ['list', 'dev', self.name]
        if filters:
            args += filters

        retval = None

        if scope:
            args += ['scope', scope]

        route_list_lines = self._run(options, tuple(args)).split('\n')
        default_route_line = next((x.strip() for x in
                                   route_list_lines if
                                   x.strip().startswith('default')), None)
        if default_route_line:
            gateway_index = 2
            parts = default_route_line.split()
            retval = dict(gateway=parts[gateway_index])
            if 'metric' in parts:
                metric_index = parts.index('metric') + 1
                retval.update(metric=int(parts[metric_index]))

        return retval

# Deprecate
def __get_gateway(iface_name=None, count=1):

    def _route(args, empty_check=False):
        if not isinstance(args, (tuple, list)) or len(args) != 3:
            raise

        cmd = "ip route | awk '%s == \"%s\" {print %s}'" % args
        retval = os.popen(cmd).read().strip()
        if empty_check and not retval:
            raise Exception("Returns value cannot be empty.")

        retval = retval.split('\n')
        
        return (retval[0] if len(retval) else None)

    retval = _route(('$1', 'default', '$3,$5'))
    if retval:
        address, iface_name = retval.split()
    elif iface_name is not None:
        address = _route(('$3', iface_name, '$9'), empty_check=True)
    else:
        raise Exception("Returns value or iface_name cannot be empty at the same time.")

    cmd = "arping -I %s -c %d -w %s %s | grep Unicast | awk -F'[][]' '{print $2}'" % (
              iface_name, count, 1.5 * count, address)
    mac_address = os.popen(cmd).read().strip()

    #if not mac_address:
    #    raise Exception("Gateway mac cannot be empty.")

    return {'ipaddr': address,
            'macaddr': mac_address,
            'iface': iface_name}

def get_gateway(default_iface=None, count=1):
    gateways = nis.gateways()

    if gateways.has_key('default'):
        addr, ifname = gateways['default'][nis.AF_INET]

        arp_cmd = "arping -I %s -c %d -w %s %s" % (
                  ifname, count, 1.5 * count, addr)
        cmd = [arp_cmd, "grep Unicast", "awk -F'[][]' '{print $2}'"]

        macaddr = os.popen('|'.join(cmd)).read().strip()

        #if not macaddr:
        #    raise Exception("Gateway mac cannot be empty.")
    else:
        addr = None
        macaddr = None
        ifname = default_iface

    return {'ipaddr': addr, 'macaddr': macaddr, 'iface': ifname}

def add_namespace_to_cmd(cmd, namespace=None):
    """Add an optional namespace to the comand."""

    return ['ip', 'netns', 'exec', namespace] + cmd if namespace else cmd

# Deprecate
def __get_address(iface_name, address=None):
    ip_device = IPDevice(iface_name)
    mac_address = ip_device.link.address

    if address is not None:
        ip_address = address
    else:
        addres = ip_device.addr.list(ip_version=4)

        if addres:
            ip_address = str(IPNetwork(addres[0]['cidr']).ip)
        else:
            ip_address = None

    return {'ipaddr': ip_address,
            'macaddr': mac_address,
            'iface': iface_name}

def get_address(iface_name, address=None):
    iface = nis.ifaddresses(iface_name)
    macaddr = iface[nis.AF_PACKET][0]['addr']

    if address is not None:
        ipaddr = address
    else:
        if iface.has_key(nis.AF_INET):
            ipaddr = iface[nis.AF_INET][0]['addr']
        else:
            ipaddr = None

    return {'ipaddr': ipaddr, 'macaddr': macaddr, 'iface': iface_name}

def get_interfaces():
    interfaces = []
    for ifname in nis.interfaces():
        for nic in NIC_PREFIX:
            if ifname.startswith(nic):
                interfaces.append(ifname)
                break

    return interfaces
