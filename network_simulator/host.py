"""This module contains all Host definition.
"""

from device import *
from event import *
from flow import *
from link import *
from statistics import *
import bisect as b


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

    def __init__(self, host, packet, packet_previously_received):
        """
        Sanity check: make sure destination was this Host and that this isn't
        a RouterPacket.
        :ivar host: Host that receives Packet
        :ivar packet: Packet received
        :ivar packet_previously_received: True if Packet previously received
        """
        Event.__init__(self)

        # Sanity check
        assert packet.dest_id == host.address and not isinstance(packet,
                                                                 RouterPacket)
        self.host = host
        self.packet = packet
        self.packet_previously_received = packet_previously_received

    def elem_in_list(elem, my_list):
        # ind is where this element *would* be inserted
        # into the list in order to keep it in sorted order.
        ind = bisect.bisect_left(my_list, elem)
        if ind != len(my_list) and my_list[ind] == elem:
            return True
        else:
            return False

    def run(self, main_event_loop, statistics):
        """
        Put packet in flow_packets_received and sort.
        Update statistics.
        :param main_event_loop: event loop where new Events will be scheduled.
        :param statistics: statistics to update
        """
        # add packet to host.flow_packets_received
        old_packets_received = self.host.flow_packets_received.get(
            self.packet.flow_id, default=list())

        self.packet_previously_received = elem_in_list(packet.packet_id,
                                                       old_packets_received)
        if not self.packet_previously_received:
            bisect.insort(old_packets_received, self.packet.packet_id)
            self.host.flow_packets_received[self.packet.flow_id] = \
                old_packets_received

        else:
            pass

        statistics.host_packet_received(self.host, self.packet,
                                        main_event_loop.global_clock_sec)

    def schedule_new_events(self, main_event_loop):
        """
        Schedule FlowReceivedAckEvent.
        Populate AckPacket for selective repeat.

        If packet was data packet, generate Ack and schedule via
        DeviceToLink event unless packet already received earlier.

        AckPackets, set original data packet's start time for RTT.
        AckPacket ID same as DataPacket ID
        :param main_event_loop: schedule new Events
        """


        if isinstance(self.packet, AckPacket):
            # look up the flow associated with this AckPacket.
            f = FlowReceivedAckEvent(self.flows[self.packet.flow_id],
                                     self.packet)
            main_event_loop.schedule_event_with_delay(f, 0.0)

        if isinstance(self.packet, DataPacket) and \
                        self.packet_id not in self.flow_packets_received:
            a_packet = AckPacket(self.packet.packet_id, self.packet.flow_id,
                                 self.host, self.packet.source_id,
                                 main_event_loop.global_clock_sec,
                                 self.host.flow_packets_received[
                                     self.flow_id], self.packet.start_time_sec)

            link = self.host.link
            d = DeviceToLinkEvent(a_packet, self.host.link, link.get_other_end(
                self.host))
            main_event_loop.schedule_event_with_delay(d, 0.0)