from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import EthAddr

log = core.getLogger()

class HostDiscovery(object):

    def __init__(self):
        core.openflow.addListeners(self)
        self.mac_to_port = {}
        self.hosts = set()
        log.info("🚀 Host Discovery Service Started Successfully")

    def _handle_ConnectionUp(self, event):
        log.info("Switch %s connected", event.dpid)

    def _handle_PacketIn(self, event):
        packet = event.parsed
        if not packet:
            return

        src = packet.src
        dst = packet.dst

        # Ignore LLDP packets
        if packet.type == packet.LLDP_TYPE:
            return

        # Learn source MAC
        self.mac_to_port[src] = event.port

        # Discover new host
        if src not in self.hosts:
            self.hosts.add(src)
            log.info("✅ New host discovered: %s on port %s", src, event.port)

        # Forwarding logic
        if dst in self.mac_to_port:
            out_port = self.mac_to_port[dst]
        else:
            out_port = of.OFPP_FLOOD

        msg = of.ofp_packet_out()
        msg.data = event.ofp
        msg.actions.append(of.ofp_action_output(port=out_port))
        msg.in_port = event.port
        event.connection.send(msg)


def launch():
    core.registerNew(HostDiscovery)