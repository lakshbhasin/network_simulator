"""This module contains all Host definition.
"""

from device import *
from event import *
from flow import *
from link import *
from statistics import *


class Host(Device):
    """
    Representation of a host.
    A host sends :class:`Packets <.Packet>` through a :class:`.Link` to a
    :class:`.Router` or a :class:`.Host`.

    :ivar dict flows: :class:`Flows <.Flow>` from this :class:`.Host`.
    :ivar link: :class:`Link` connected to this :class:`.Host`.
    :ivar flow_packets_received: a map from flow ID to a sorted list of the
    packet IDs that have been received for that Flow. This is used to carry
    out "selective repeat" instead of "go-back-N".
    """
    def __init__(self, address=None, flows={}, flow_packets_received={},
                 link=None):
        Device.__init__(self, address)
        self.flows = flows
        self.flow_packets_received = flow_packets_received
        self.link = link


class HostReceivedPacketEvent(Event):
    """
    Host receives packets from a flow.
    """

    def __init__(self, host, packet):
        """
        Sanity check: make sure destination was this Host and that this isn't
        a RouterPacket.
        :ivar host: host that receives packet
        :ivar packet: packet received
        """
        Event.__init__(self)

        # Sanity check
        assert packet.dest_id == host and \
        packet.packet_id != ROUTER_PACKET_DEFAULT_ID

        self.host = host
        self.packet = packet

    def run(self, main_event_loop, statistics):
        """
        Put packet in flow_packets_received and sort.
        Update statistics.
        :param main_event_loop: event loop where new Events will be scheduled.
        :param statistics: statistics to update
        """
        # add packet to host.flow_packets_received
        self.flow_packets_received[self.packet.flow_id] = self.packet.packet_id
        self.flow_packets_received.sort()
        
        statistics.host_packet_received(self.host, self.packet,
                                        main_event_loop.global_clock_sec)

    def schedule_new_events(self, main_event_loop):
        """
        If packet was Ack, look up Flow and say packet was received.
        Schedule FlowReceivedAckEvent.
        Populate AckPacket for selective repeat.

        If packet was data packet, generate Ack and schedule via
        DeviceToLink event unless packet already received earlier.

        Ackpackets, set original data packet's start time for RTT.
        AckPacket ID same as DataPacket ID
        :param main_event_loop: schedule new Events
        :param statistics: update statistics
        """

        if isinstance(self.packet, AckPacket):
            main_event_loop.schedule_new_event_with_delay(self, self.flow,
                                                          self.packet)
            ack_flow_id = self.packet.flow_id
            for i in self.flow_packets_received:
                if self.flow_packets_received[i].flow_id == ack_flow_id:
                    self.flow_packets_received[i].packet_id = self.packet_id
        if isinstance(self.packet, DataPacket) and \
                        self.packet_id not in self.flow_packets_received:
            a_packet = AckPacket(self.packet)
            DeviceToLinkEvent(a_packet, self.link, dest_dev)