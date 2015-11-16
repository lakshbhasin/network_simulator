"""This module contains all Host definition.
"""

import bisect
import logging

from device import *
from event import *
from flow import *
from link import *
from statistics import *

logger = logging.getLogger(__name__)


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
        self.packet_previously_received = False

    def run(self, main_event_loop, statistics):
        """
        Put packet in flow_packets_received and sort.
        Update statistics.
        :param main_event_loop: event loop where new Events will be scheduled.
        :param statistics: statistics to update
        """
        # add packet to host.flow_packets_received if its a DataPacket
        if isinstance(self.packet, DataPacket):

            old_packets_received = self.host.flow_packets_received.get(
                self.packet.flow_id, default=list())

            self.packet_previously_received = elem_in_list(
                self.packet.packet_id, old_packets_received)

            if not self.packet_previously_received:
                bisect.insort(old_packets_received, self.packet.packet_id)
                self.host.flow_packets_received[self.packet.flow_id] = \
                    old_packets_received

            else:
                logger.debug("Packet %d was already received",
                             self.packet.packet_id)

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
            flow_ack_ev = FlowReceivedAckEvent(self.flows[
                                                   self.packet.flow_id],
                                               self.packet)
            main_event_loop.schedule_event_with_delay(flow_ack_ev, 0.0)

        if isinstance(self.packet, DataPacket) and not \
                self.packet_previously_received:
            a_packet = AckPacket(packet_id=self.packet.packet_id,
                                 flow_id=self.packet.flow_id,
                                 source_id=self.host.address,
                                 dest_id=self.packet.source_id,
                                 start_time_sec=
                                 main_event_loop.global_clock_sec,
                                 flow_packets_received=
                                 self.host.flow_packets_received[self.flow_id],
                                 data_packet_start_time_sec=
                                 self.packet.start_time_sec)

            link = self.host.link
            dev_link_ev = DeviceToLinkEvent(a_packet, link, link.get_other_end(
                self.host))
            main_event_loop.schedule_event_with_delay(dev_link_ev, 0.0)


def elem_in_list(elem, my_list):
    """
    This function takes an element and a list, and returns True if elem
    is in the list, and False if it is not in the list.
    :param elem: the element to be checked
    :param my_list: the list where the element is placed into
    """
    # ind is where this element *would* be inserted
    # into the list in order to keep it in sorted order.
    ind = bisect.bisect_left(my_list, elem)
    return ind != len(my_list) and my_list[ind] == elem