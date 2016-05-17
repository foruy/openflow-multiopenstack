from oslo.config import cfg

from ryu.lib.packet import arp
from ryu.lib.packet import ethernet
from ryu.lib.packet import packet
from ryu.lib import addrconv
from ryu.ofproto import ether

from daoliagent.services.base import PacketBase
from daoliagent.lib import SMAX
from daoliagent.openstack.common import log as logging

CONF = cfg.CONF

LOG = logging.getLogger(__name__)

class PacketARP(PacketBase):
    priority = 5

    def _arp(self, msg, dp, in_port, pkt_ether, pkt_arp, address):
        ofp, ofp_parser, ofp_set, ofp_out = self.ofp_get(dp)
        actions = [ofp_parser.OFPActionSetField(eth_src=address),
                   ofp_parser.OFPActionOutput(ofp.OFPP_IN_PORT)]

        match = ofp_parser.OFPMatch(
            in_port=in_port, eth_type=ether.ETH_TYPE_ARP,
            arp_spa=pkt_arp.src_ip, arp_tpa=pkt_arp.dst_ip)

        LOG.debug("arp response %(src_mac)s-%(src_ip)s -> %(dst_mac)s-%(dst_ip)s",
                  {'src_mac': address, 'src_ip': pkt_arp.dst_ip,
                   'dst_mac': pkt_arp.src_mac, 'dst_ip': pkt_arp.src_ip})
        self.add_flow(dp, match, actions)
        self.packet_out(msg, dp, actions)

    def _redirect(self, msg, dp, in_port, pkt_ether, pkt_arp, output):
        ofp, ofp_parser, ofp_set, ofp_out = self.ofp_get(dp)
        actions = [ofp_parser.OFPActionOutput(output)]

        match = ofp_parser.OFPMatch(
            in_port=in_port, eth_type=ether.ETH_TYPE_ARP,
            arp_spa=pkt_arp.src_ip, arp_tpa=pkt_arp.dst_ip)

        self.add_flow(dp, match, actions)
        self.packet_out(msg, dp, actions)

    def run(self, msg, pkt_ether, pkt_arp, gateway, **kwargs):
        dp = msg.datapath
        in_port = msg.match['in_port']
        ofp, ofp_parser, ofp_set, ofp_out = self.ofp_get(dp)

        src_mac = pkt_arp.src_mac
        dst_ip = pkt_arp.dst_ip
        LOG.debug("arp request %(src_mac)s-%(src_ip)s -> %(dst_mac)s-%(dst_ip)s",
                  {'src_mac': src_mac, 'src_ip': pkt_arp.src_ip,
                   'dst_mac': pkt_arp.dst_mac, 'dst_ip': dst_ip})

        if gateway.int_dev != gateway.ext_dev:
            int_port = self.port_get(dp, devname=gateway.int_dev)
            tap_port = self.port_get(dp, devname=gateway.vint_dev)

            if not int_port or not tap_port:
                return True

            if in_port == int_port.port_no:
                if pkt_arp.dst_ip == gateway['int_ip']:
                    self._redirect(msg, dp, in_port, pkt_ether, pkt_arp, tap_port.port_no)
                return True

            if in_port == tap_port.port_no:
                if pkt_arp.src_ip == gateway['int_ip']:
                    self._redirect(msg, dp, in_port, pkt_ether, pkt_arp, int_port.port_no)
                return True

        port = self.port_get(dp, devname=gateway['ext_dev'])
        if not port:
            return True

        if in_port == port.port_no:
            if pkt_arp.dst_ip == gateway['ext_ip']:
                self._redirect(msg, dp, in_port, pkt_ether, pkt_arp, ofp.OFPP_LOCAL)
            return True

        if in_port == ofp.OFPP_LOCAL:
            if pkt_arp.src_ip == gateway['ext_ip']:
                self._redirect(msg, dp, in_port, pkt_ether, pkt_arp, port.port_no)
            return True

        num_ip = addrconv.ipv4._addr(dst_ip).value

        if pkt_arp.opcode != arp.ARP_REQUEST:
            LOG.debug("unknown arp op %s", pkt_arp.opcode)
        elif (num_ip & 0x0000FFFF == SMAX - 1):
            #br_port = self.port_get(dp, devname=gateway['vext_dev'])
            #self._arp(dp, in_port, pkt_ether, pkt_arp, br_port.hw_addr)
            self._arp(msg, dp, in_port, pkt_ether, pkt_arp, gateway['vint_mac'])
        else:
            servers = self.db.server_get_by_mac(src_mac, dst_ip, False)
            if servers['src'] and servers['dst']:
                self._arp(msg, dp, in_port, pkt_ether, pkt_arp, servers['dst'].mac_address)
            else:
                self._arp(msg, dp, in_port, pkt_ether, pkt_arp, gateway['vint_mac'])
