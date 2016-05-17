import os
from oslo.config import cfg

from daoliproxy.linux import ip_lib

network_opts = [
    cfg.StrOpt('br_dev', default='br-int'),
    cfg.StrOpt('tap_dev', default='br-tap'),
    cfg.StrOpt('ext_dev', default=os.environ.get('ext_dev')),
    cfg.StrOpt('int_dev', default=os.environ.get('int_dev')),
]

CONF = cfg.CONF
CONF.register_opts(network_opts)

class Network:
    def __init__(self):
        self.br_name = CONF.br_dev
        self._init_network()

    def _init_network(self):
        ifaces = ip_lib.get_interfaces()
        ifaces.sort(reverse=True)

        if len(ifaces) < 1:
            raise Exception("Network card could not be found")

        self.ext_dev = CONF.get('ext_dev')

        if not self.ext_dev:
            self.ext_dev = ifaces[-1]
        else:
            if self.ext_dev not in ifaces:
                raise Exception("Device[%s] not found" % self.ext_dev)

        self.int_dev = CONF.get('int_dev')

        if not self.int_dev:
            if len(ifaces) == 1:
                self.int_dev = self.ext_dev
            else:
                self.int_dev = ifaces[-2]
        else:
            if self.int_dev not in ifaces:
                raise Exception("Device[%s] not found" % self.int_dev)
            
        self.tap_dev = CONF.tap_dev

    def gateway_get(self):
        info = {}
        info['idc_mac'] = ip_lib.get_gateway(self.br_name)['macaddr']

        exter = ip_lib.get_address(self.ext_dev)
        info['vext_dev'] = self.br_name
        info['ext_dev'] = exter['iface']
        info['ext_mac'] = exter['macaddr']
        info['ext_ip'] = ip_lib.get_address(self.br_name)['ipaddr'] \
                or exter['ipaddr']

        info['datapath_id'] = '0000' + info['ext_mac'].replace(':', '')

        if self.int_dev == self.ext_dev:
            info['int_dev'] = info['ext_dev']
            info['int_mac'] = info['ext_mac']
            info['int_ip'] = info['ext_ip']
        else:
            taper = ip_lib.get_address(self.tap_dev)
            inter = ip_lib.get_address(self.int_dev)
            info['int_dev'] = inter['iface']
            info['int_mac'] = inter['macaddr']
            info['int_ip'] = taper['ipaddr'] or inter['ipaddr']

        info['vext_ip'] = info['ext_ip']
        info['vint_dev'] = self.tap_dev
        info['vint_mac'] = info['int_mac']

        return info
