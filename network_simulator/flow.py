"""
Module for the abstract Flow class, its subclasses (which implement various
TCP algorithms), and Flow-related Events.
"""

from abc import ABCMeta, abstractmethod
from Queue import PriorityQueue

from common import *
from event import *
from link import *
from main_event_loop import *
from packet import *

class Flow(object):
    """
    Representation of general (abstract) Flow. Subclasses implement specific
    TCP algorithms.
    """
    __metaclass__ = ABCMeta

    def __init__(self, flow_id=None, source_addr=None, dest_addr=None,
                 source=None, dest=None, window_size_packets=None,
                 packets_in_transit=set(), packet_rtts=list(),
                 data_size_bits=None, start_time_sec=None):
        """
        :ivar string flow_id: unique string ID for this Flow.
        :ivar string source_addr: address of source Host.
        :ivar string dest_addr: address of destination Host.
        :ivar Host source: source Host.
        :ivar Host dest: dest Host.
        :ivar int window_size_packets:
        :ivar set<int> packets_in_transit: set of packet IDs in transit
        :ivar list packet_rtts: list of (packet_id, rtt) tuples that stores
        the RTT for each Packet that completed a round trip.
        :ivar int data_size_bits: total amount of data to transmit in bits.
        Assumed to be a multiple of the DataPacket size.
        :ivar float start_time_sec: start time relative to global clock.
        :return:
        """
        self.flow_id = flow_id
        self.source_addr = source_addr
        self.dest_addr = dest_addr
        self.source = source
        self.dest = dest
        self.window_size_packets = window_size_packets
        self.packets_in_transit = packets_in_transit
        self.packet_rtts = packet_rtts
        self.data_size_bits = data_size_bits
        self.start_time_sec = start_time_sec

    def packet_id_exceeds_data(self, packet_id):
        """
        Checks if a DataPacket's ID is will exceed the amount of data to
        check. If so, this packet ID is too large and should not be sent.
        :param int packet_id: zero-indexed Packet ID
        :return: True if Packet ID exceeds data size, else False
        """
        return (packet_id + 1) * DATA_PACKET_SIZE_BITS > self.data_size_bits

    def get_window_size(self):
        """
        :return: current window size in packets
        """
        return self.window_size_packets

    @abstractmethod
    def handle_packet_loss(self, packet_id, main_event_loop):
        """
        A handler function that is called after a packet loss, which can
        either be:
            1) A timeout
            2) A single ACK that indicates the given packet is missing (logic
               for dealing with multiple dupACKs will be in Flow subclasses)
        If necessary, this flow can directly add Events to the MainEventLoop.
        :param int packet_id: lost Packet's ID.
        :param MainEventLoop main_event_loop: main Event loop for further
        Event scheduling.
        """
        pass

    @abstractmethod
    def handle_packet_success(self, packet_id):
        """
        A handler for dealing with packets that successfully completed a
        round trip. This will adjust window sizes and make other state
        changes, depending on the TCP congestion algorithm.
        :param packet_id: ID of packet that completed a round trip
        """
        pass

    def __repr__(self):
        return str(self.__dict__)


class InitiateFlowEvent(Event):
    """
    An one-time Event called to set up the Flow at a given timestamp.
    """
    def __init__(self, flow=None):
        """
        :ivar Flow flow: flow of this event.
        :ivar list packet_ids: a list of integers of packet IDs. The list
        is to be determined later.
        :ivar list packets_to_send: list of data packets to send. This is
        default to an empty list. This list will be populated later.
        """
        self.flow = flow
        self.packet_ids = []
        self.packets_to_send = []

    def run(self, main_event_loop, statistics):
        """
        Set up a list of data packets to initiate a flow.

        :param MainEventLoop main_event_loop: main loop to retrieve the
        simulation time of function call.
        :param Statistics statistics: the Statistics to update.
        """
        # Create a list of packet_ids by going through the window size.
        self.packet_ids = []
        for new_id in range(0, self.flow.get_window_size()):
            self.packet_ids.append(new_id)
        for curr_packet in self.packet_ids:
            if not self.flow.packet_id_exceeds_data(curr_packet):
                new_data_packet = DataPacket(curr_packet.packet_id,
                                             self.flow.flow_id,
                                             self.flow.source_addr,
                                             self.flow.dest_addr,
                                             main_event_loop.global_clock_sec)
                self.packets_to_send.append(new_data_packet)

    def schedule_new_events(self, main_event_loop):
        """
        Schedule a FlowSendPacketsEvent immediately, with the list of packets
        to send.

        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        if not self.packets_to_send:
            # We are out of packets to send. Send Complete Event.
            flow_complete = FlowCompleteEvent(self.flow)
            main_event_loop.schedule_event_with_delay(flow_complete, 0.0)
            return

        flow_send_event = FlowSendPacketsEvent(self.flow,
                                               self.packets_to_send)
        main_event_loop.schedule_event_with_delay(flow_send_event, 0.0)


class FlowSendPacketsEvent(Event):
    """
    Send data packet from a flow.
    """
    def __init__(self, flow, packets_to_send):
        """
        :ivar Flow flow: flow of this event.
        :ivar list packets_to_send: list of data packets to send.
        """
        self.flow = flow
        self.packets_to_send = packets_to_send

    def run(self, main_event_loop, statistics):
        """
        Check that the size of packets combined is smaller than
        the window size.
        :param MainEventLoop main_event_loop: main loop.
        :param Statistics statistics: the Statistics to update.
        """
        if len(set(self.flow.packets_in_transit).union(
            set(self.flow.packets_to_send))) \
            > self.flow.get_window_size():
            raise ValueError("The size of packets combiend "
                             "is greater than the window size in flow")

        for curr_packet in self.packets_to_send:
            if curr_packet.packet_id not in self.flow.packets_in_transit:
                self.flow.packets_in_transit.add(curr_packet.packet_id)

    def schedule_new_events(self, main_event_loop):
        """
        Schedule FlowSendPacketsEvent for timed out packets.

        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        # TODO(sharon): Need to fix the initialization after Link subclasses
        # have been implemented.
        for curr_packet in self.packets_to_send:
            device_link_event = DeviceToLinkEvent(curr_packet, False)
            main_event_loop.schedule_event_with_delay(device_link_event, 0.0)

        # Schedule FlowTimeoutPacketEvent for each packet, which will occur
        # in FLOW_TIMEOUT_SEC from now.
        for curr_packet in self.packets_to_send:
            timeout_event = FlowTimeoutPacketEvent(self.flow, curr_packet)
            main_event_loop.schedule_event_with_delay(timeout_event,
                                                      FLOW_TIMEOUT_SEC)


class FlowTimeoutPacketEvent(Event):
    """
    Triggered when packet has timeout at a flow.
    """
    def __init__(self, flow, packet):
        """
        :ivar Flow flow: flow of this event.
        :ivar packet packet: the particular packet of this timeout.
        """
        self.flow = flow
        self.packet = packet

    def run(self, main_event_loop, statistics):
        # Does nothing.
        pass

    def schedule_new_events(self, main_event_loop):
        """
        Check if a packet is in transit. If so, retransmit because it might
        be lost.

        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        # If the particular packet is currently not in transit, then we don't
        # need to do anything here.
        if self.packet.packet_id not in self.flow.packets_in_transit:
            return
        self.flow.handle_packet_loss(self.packet.packet_id, main_event_loop)
        flow_send_event = FlowSendPacketsEvent(self.flow, [self.packet])
        main_event_loop.schedule_event_with_delay(flow_send_event, 0.0)


class FlowReceivedAckEvent(Event):
    """
    Triggered when an ACK is received by a flow.
    """
    def __init__(self, flow, packet):
        """
        :ivar Flow flow: flow of this event.
        :ivar AckPacket packet: ack packet received.
        :ivar int last_packet_id: store last packet id to help re-scheduling.
        :ivar boolean had_packet_loss: if this event has ever lost a packet.
        """
        self.flow = flow
        self.packet = packet
        self.last_packet_id = None
        self.had_packet_loss = False

    def run(self, main_event_loop, statistics):
        """
        Triggered whenever an ACK is received.

        :param MainEventLoop main_event_loop: main loop to retrieve the
        simulation time of function call.
        :param Statistics statistics: the Statistics to update.
        """
        # Update RTT.
        sent_time = self.packet.data_packet_start_time_sec
        curr_rtt = main_event_loop.global_clock_sec - sent_time
        self.flow.packet_rtts.append((self.packet.packet_id, curr_rtt))

        # Store and remove packet in transit.
        self.last_packet_id = max(self.flow.packets_in_transit)
        self.flow.packets_in_transit.remove(self.packet.packet_id)

        self.flow.handle_packet_success(self.packet_id)

        # TODO(sharon): Base on following description, update the code when
        # we have finished TCP algorithm setup.
        # If there is a gap or duplicate in the list of sent packets by ACK,
        # then that means that a packet was lost (since we are using selective
        # repeat). Update window_size accordingly based on TCP algorithm.
        # gap = Packet()
        # if gap is None:
        #     return
        # self.had_packet_loss = True
        # self.flow.handle_packet_loss(gap.packet_id, main_event_loop)

        # 3. If there is no gap, then there was no packet loss. Update
        # window_size based on TCP algorithm.
        #

    def schedule_new_events(self, main_event_loop):
        """
        Schedule Flow event based on packet loss.

        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        if self.had_packet_loss:
            return
        # gap = a packet loss (gap in ACK or dupACK)
        # TODO(sharon): Change this once we have TCP to find gap.
        new_packet = None
        if not new_packet:
            # Find the highest ID packet in packets_in_transit and go one more
            # than that.
            new_packet_id = self.last_packet_id + 1
            if self.flow.packet_id_exceeds_data(new_packet_id):
                # We are out of packets to send. Send Complete Event.
                flow_complete = FlowCompleteEvent(self.flow)
                main_event_loop.schedule_event_with_delay(flow_complete, 0.0)
                return

            new_packet = DataPacket(new_packet_id, self.flow.flow_id,
                                    self.flow.source_addr, self.flow.dest_addr,
                                    main_event_loop.global_clock_sec)

        # Schedule a FlowSendPacketsEvent with gap or new max packet.
        flow_send_event = FlowSendPacketsEvent(self.flow, [new_packet])
        main_event_loop.schedule_event_with_delay(flow_send_event, 0.0)


class FlowCompleteEvent(Event):
    """
    Triggered packet ID exceeds data size or we have no more packets to send.
    """
    def __init__(self, flow):
        self.flow = flow

    def run(self, main_event_loop, statistics):
        """
        :param MainEventLoop main_event_loop: main loop to retrieve the
        simulation time of function call.
        :param Statistics statistics: the Statistics to update.
        """
        # Do nothing.
        pass

    def schedule_new_events(self, main_event_loop):
        """
        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        # Do nothing.
        pass


# TODO(team): Flow subclasses for at least two TCP algorithms.