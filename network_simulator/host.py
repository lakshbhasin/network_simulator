"""This module contains all Host definition.
"""

import inspect
from device import *


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

    def run(self, main_event_loop, statistics):
        """
        Sanity check: make sure the destination was this Host,
        and that this isn’t a RouterPacket. Update statistics.

        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        :param Statistics statistics: the Statistics to update
        """
        if inspect.isclass(self.flow_packets_received) == RouterPacket:
            raise ValueError ("Packet received is a router packet.")
        if self.flow_packets_received.dest_addr != self.address:
            raise ValueError ("Destination was not this host.")
        else:
            #check statistics?
            pass

    def schedule_new_events(self, main_event_loop, statistics):
        """
        If the packet was an ACK, look up the corresponding Flow and let it
        know that its packet was received.
        Schedule a FlowReceivedAckEvent immediately.
        Populate the AckPacket for selective repeat later.

        If the packet was a data packet, generate a corresponding ACK and
        schedule it via a DeviceToLink event unless that packet was already
        received earlier by this Host.

        For AckPackets, need to set original data packet’s start time so we can
        calculate RTT later.
        Also AckPacket’s ID should be the original DataPacket’s ID.

        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        :param Statistics statistics: the Statistics to update
        """
        if inspect.isclass(self.flow_packets_received) == AckPacket:
            event.schedule_new_events(self, main_event_loop)
            flow.handle_packet_success(self, packet_id)
        if inspect.isclass(self.flow_packets_received) == DataPacket and \
                        packet_id not in self.flow_packets_received:
            event.schedule_new_events(self, DeviceToLink)
        else:
            #check statistics?
            pass