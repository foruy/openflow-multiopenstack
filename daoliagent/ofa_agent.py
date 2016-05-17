import os
import struct
from webob import Response

from oslo.config import cfg

from ryu.app.wsgi import route
from ryu.app.wsgi import ControllerBase, WSGIApplication
from ryu.base import app_manager
from ryu.controller import dpset
from ryu.controller import handler
from ryu.controller.handler import set_ev_cls
from ryu.controller import ofp_event
from ryu.lib import dpid as dpid_lib
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ryu.lib.packet import udp
from ryu.lib.packet import icmp
from ryu.lib.packet import ethernet
from ryu.lib.packet import packet
from ryu.ofproto import inet
#from ryu.ofproto import ofproto_v1_3 as ryu_ofp13
from ryu.ofproto import ofproto_v1_2 as ryu_ofp12

from daoliagent.db import base as db_base
from daoliagent.openstack.common.gettextutils import _LI
from daoliagent.openstack.common import log as logging
from daoliagent.objects import GatewayState
from daoliagent.objects import PortState
from daoliagent.services import PacketGroup, PacketARP, PacketIPv4

try:
    import json
except ImportError:
    import simplejson as json

idc_opt = cfg.IntOpt('idc_id',
                     default=os.environ.get('idc_id', 0),
                     help="Default idc identification")

CONF = cfg.CONF
CONF.register_opt(idc_opt)
CONF.register_opt(cfg.IntOpt('timeout', default=40))
LOG = logging.getLogger(__name__)

class GroupController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(GroupController, self).__init__(req, link, data, **config)
        self.app = data['app']

    @route('group', '/v1.0/group', methods=['PUT'])
    def delete(self, _req, **kwargs):
        body = json.loads(_req.body)

        if not body.has_key('sid') or not body.has_key('did'):
            return Response(status=400)

        self.app.group_delete(body['sid'], body['did'])
        return Response(status=200)

class OFAgentRyuApp(app_manager.RyuApp):
    OFP_VERSIONS = [ryu_ofp12.OFP_VERSION]
    _CONTEXTS = {'dpset': dpset.DPSet,
                 'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(OFAgentRyuApp, self).__init__(*args, **kwargs)
        self.port_state = {}
        self.dps = kwargs['dpset'].dps
        self.packetlib = PacketLib(self)
        kwargs['wsgi'].register(GroupController, {'app': self.packetlib})

    @handler.set_ev_cls(dpset.EventDP)
    def dp_hadler(self, ev):
        dpid = ev.dp.id
        if ev.enter:
            if dpid not in self.port_state:
                self.port_state[dpid] = PortState()
                for port in ev.ports:
                    self.port_state[dpid].add(port)
            self.packetlib.init_flow(ev.dp)
        else:
            if dpid in self.port_state:
                for port in self.port_state[dpid].values():
                    self.port_state[dpid].remove(port)
                del self.port_state[dpid]

    @handler.set_ev_cls(dpset.EventPortAdd)
    def port_add_handler(self, ev):
        self.port_state[ev.dp.id].add(ev.port)

    @handler.set_ev_cls(dpset.EventPortDelete)
    def port_del_handler(self, ev):
        self.port_state[ev.dp.id].remove(ev.port)

    @handler.set_ev_cls(dpset.EventPortModify)
    def port_mod_handler(self, ev):
        self.port_state[ev.dp.id].add(ev.port)

    @set_ev_cls(ofp_event.EventOFPPacketIn, handler.MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        try:
            self.packetlib.packet_in_handler(ev)
        except Exception as e:
            LOG.error(e)

class PacketLib(db_base.Base):

    def __init__(self, ryuapp):
        super(PacketLib, self).__init__()
        self.gateway = GatewayState(self.db.gateway_get_all())
        self.packet_arp = PacketARP(self, ryuapp)
        self.packet_ipv4 = PacketIPv4(self, ryuapp)
        self.packet_group = PacketGroup(self, ryuapp)
        self.flows = {}

    def gateway_get(self, dpid):
        normal_dpid = dpid_lib.dpid_to_str(dpid)
        gateway = self.gateway.get(normal_dpid)
        if not gateway:
            gateway = self.db.gateway_get_by_datapath(normal_dpid)
            if gateway:
                self.gateway.add(gateway)
        return gateway

    def packet_in_handler(self, ev):
        """Check a packet-in message.

           Build and output a packet-out.
        """
        msg = ev.msg
        datapath = msg.datapath
        port = msg.match['in_port']
        gateway = self.gateway_get(datapath.id)

        if gateway is None:# or gateway.idc_id != CONF.idc_id:
            return

        pkt = packet.Packet(msg.data)
        pkt_ethernet = pkt.get_protocol(ethernet.ethernet)

        if not pkt_ethernet:
            LOG.info(_LI("drop non-ethernet packet"))
            return

        pkt_arp = pkt.get_protocol(arp.arp)
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)

        if pkt_arp:
            self.packet_arp.run(msg, pkt_ethernet, pkt_arp, gateway)
        elif pkt_ipv4:
            pkt_tp = pkt.get_protocol(tcp.tcp) or \
                     pkt.get_protocol(udp.udp) or \
                     pkt.get_protocol(icmp.icmp)

            if pkt.get_protocol(icmp.icmp):
                 LOG.error("packet-in msg %s %s %s from %s", datapath.id, pkt_ipv4, pkt_tp, port)
            LOG.debug("packet-in msg %s %s %s from %s", 
                      datapath.id, pkt_ipv4, pkt_tp, port)

            if pkt_tp and port:
                self.packet_ipv4.run(msg, pkt_ethernet, pkt_ipv4, pkt_tp, gateway)
        else:
            LOG.debug(_LI("drop non-arp and non-ip packet"))

    def init_flow(self, dp):
        gateway = self.gateway_get(dp.id)

        if gateway is not None:# and gateway.idc_id == CONF.idc_id:
            self.packet_group.init_flow(dp, gateway)

    def group_delete(self, sid, did):
        src = self.db.server_get(sid, gateway=True)
        dst = self.db.server_get(did, gateway=True)

        if any((not src, not dst, not src.Instance.address,
                not dst.Instance.address)):
            LOG.warn("Gateway or Instance could be not found.")
        else:
            self.packet_group.run(src.Instance, src.Gateway,
                                  dst.Instance, dst.Gateway)
