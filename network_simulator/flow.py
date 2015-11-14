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


class PacketLossType(object):
    """
    An enum for describing different kinds of Packet losses, as detected by
    the Flow that sent the Packet.
    """
    # AckPacket not received after FLOW_TIMEOUT_SEC seconds.
    TIMEOUT = 0

    # Gap in AckPacket's selective repeat data
    GAP_ACK = 1


class Flow(object):
    """
    Representation of general (abstract) Flow. Subclasses implement specific
    TCP algorithms.
    """
    __metaclass__ = ABCMeta

    def __init__(self, flow_id=None, source_addr=None, dest_addr=None,
                 source=None, dest=None,
                 window_size_packets=INITIAL_WINDOW_SIZE_PACKETS,
                 packets_in_transit=set(), packet_rtts=list(),
                 data_size_bits=None, start_time_sec=None):
        """
        :ivar string flow_id: unique string ID for this Flow.
        :ivar string source_addr: address of source Host.
        :ivar string dest_addr: address of destination Host.
        :ivar Host source: source Host.
        :ivar Host dest: dest Host.
        :ivar int window_size_packets: The maximum number of packets that can be
        in transit at a given time.
        :ivar set<int> packets_in_transit: set of packet IDs that are either
        currently in transit, or *scheduled* to be in transit.
        :ivar list packet_rtts: list of (packet_id, rtt) tuples that stores
        the RTT for each Packet that completed a round trip.
        :ivar Queue<int> packet_id_buffer: a FIFO Queue of Packet IDs that are
        buffered up to send, but have *not* yet been sent because the window
        size is too small. Useful for when losses occur but window size small.
        :ivar int data_size_bits: total amount of data to transmit in bits.
        Assumed to be a multiple of the DataPacket size.
        :ivar float start_time_sec: start time relative to global clock.
        :ivar int max_packet_id_sent: the maximum DataPacket ID that has been
        sent (might not have been ACK'd yet).
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
        self.packet_id_buffer = Queue()
        self.max_packet_id_sent = -1  # so first ID sent is 0.

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

    def get_next_data_packet_id(self, peek=False):
        """
        Helper function to get the next DataPacket ID to *send*. This works by:
            1) Taking the head element in the packet ID buffer. Or...
            2) Taking max_packet_id_sent + 1

        :param bool peek: If False, self.max_packet_id_sent is updated.
        :return: int (next DataPacket's ID)
        """
        if not self.packet_id_buffer.empty():
            next_packet_id = self.packet_id_buffer.get_nowait()
        else:
            next_packet_id = self.max_packet_id_sent + 1

        if not peek:
            self.max_packet_id_sent = max(self.max_packet_id_sent,
                                          next_packet_id)

        return next_packet_id

    @abstractmethod
    def handle_packet_loss(self, packet_id, loss_type, main_event_loop):
        """
        A handler function that is called after a packet loss, which can
        either be:
            1) A timeout
            2) A single ACK that indicates the given packet is missing (logic
               for dealing with repeated gaps will be in Flow subclasses)
        If necessary, this flow can directly add Events to the MainEventLoop.

        Note: If a packet loss occurs but the max window size of the flow has
        already been reached, we can't retransmit. In these cases, the packet is
        added to a buffer.

        :param int packet_id: lost Packet's ID.
        :param PacketLossType loss_type: the kind of packet loss that occurred.
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


# TODO(laksh): Flow subclasses for at least two TCP algorithms.
# TODO(laksh): handle_packet_loss needs to schedule events for timeouts and
# other losses as well; this is not handled directly in the Event code. Must
# schedule FlowSendPacketsEvent.
# TODO(laksh): handle_packet_loss may have to interact with Packet ID buffer
# if window size is already reached. Buffer is read from after ACKs received.
# TODO(laksh): Need a periodic Event for TCP FAST window size updates. This
# will also schedule new FlowSendPacketsEvents if there is enough space in
# the new window.


class InitiateFlowEvent(Event):
    """
    A one-time Event called to set up the Flow at a given timestamp.
    """
    def __init__(self, flow=None):
        """
        :ivar Flow flow: flow of this event.
        :ivar list packets_to_send: list of data packets to send. This is
        default to an empty list. This list will be populated later.
        """
        super(InitiateFlowEvent, self).__init__()
        self.flow = flow
        self.packets_to_send = []

    def run(self, main_event_loop, statistics):
        """
        Set up a list of data packets to initiate a flow.

        :param MainEventLoop main_event_loop: main loop to retrieve the
        simulation time of function call.
        :param Statistics statistics: the Statistics to update.
        """
        # Get Packet IDs until the window size is met.
        packet_ids = []
        while len(packet_ids) < self.flow.get_window_size():
            next_packet_id = self.flow.get_next_data_packet_id()
            packet_ids.append(next_packet_id)

        for curr_packet_id in packet_ids:
            if not self.flow.packet_id_exceeds_data(curr_packet_id):
                new_data_packet = DataPacket(packet_id=curr_packet_id,
                                             flow_id=self.flow.flow_id,
                                             source_id=self.flow.source_addr,
                                             dest_id=self.flow.dest_addr,
                                             start_time_sec=
                                             main_event_loop.global_clock_sec)
                self.packets_to_send.append(new_data_packet)

    def schedule_new_events(self, main_event_loop):
        """
        Schedule a FlowSendPacketsEvent immediately, with the list of packets
        to send.

        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        flow_send_event = FlowSendPacketsEvent(self.flow,
                                               self.packets_to_send)
        main_event_loop.schedule_event_with_delay(flow_send_event, 0.0)


class FlowSendPacketsEvent(Event):
    """
    Sends a list of DataPackets from a flow.
    """
    def __init__(self, flow, packets_to_send):
        """
        Sets up an Event to send Packets, and also records these Packets in
        the Flow's packets_in_transit variable immediately.

        Precondition: Sending these Packets will not cause the Flow's current
        window size to be exceeded.

        :ivar Flow flow: flow of this event.
        :ivar list packets_to_send: list of data packets to send.
        """
        super(FlowSendPacketsEvent, self).__init__()
        self.flow = flow
        self.packets_to_send = packets_to_send

        # We want packets_in_transit to reflect Packets that are scheduled to
        # be sent as well, to avoid race conditions.
        for curr_packet in self.packets_to_send:
            self.flow.packets_in_transit.add(curr_packet.packet_id)

        # Sanity check that packets_in_transit is not too big now.
        if len(self.flow.packets_in_transit) > self.flow.get_window_size():
            # This should never happen since we have a Packet ID buffer in
            # place.
            raise ValueError("The size of packets in transit + scheduled "
                             "is greater than the Flow's window size")

    def run(self, main_event_loop, statistics):
        """
        Update statistics only.
        :param MainEventLoop main_event_loop: main loop.
        :param Statistics statistics: the Statistics to update.
        """
        # TODO(team): Update stats
        pass

    def schedule_new_events(self, main_event_loop):
        """
        Schedule FlowSendPacketsEvent for timed out packets.

        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        for curr_packet in self.packets_to_send:
            # Send packets on this Flow's Host's Link, to whatever's on the
            # other side.
            link = self.flow.source.link
            dest_dev = link.get_other_end(self.flow.source)
            device_link_event = DeviceToLinkEvent(packet=curr_packet,
                                                  link=link,
                                                  dest_dev=dest_dev)
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
        super(FlowTimeoutPacketEvent, self).__init__()
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
        # If the particular packet is currently not in transit (i.e. has
        # returned and been ACK'd), then we don't need to do anything here.
        if self.packet.packet_id not in self.flow.packets_in_transit:
            return

        # handle_packet_loss() will schedule additional Events.
        self.flow.handle_packet_loss(self.packet.packet_id,
                                     PacketLossType.TIMEOUT,
                                     main_event_loop)


class FlowReceivedAckEvent(Event):
    """
    Triggered when an ACK is received by a flow.
    """
    def __init__(self, flow, packet):
        """
        :ivar Flow flow: flow of this event.
        :ivar AckPacket packet: ack packet received.
        :ivar list<int> lost_packet_ids: Packet IDs that were determined to
        be lost based on gaps.
        """
        super(FlowReceivedAckEvent, self).__init__()
        assert isinstance(packet, AckPacket)
        self.flow = flow
        self.packet = packet
        self.lost_packet_ids = []

    def find_missing_packets(self):
        """
        Based on the flow_packets_received parameter returned by an
        AckPacket, return a list of the missing packet IDs (i.e. the gaps).
        It is assumed that flow_packets_received is in ascending sorted
        order, and that packet IDs are zero-indexed.
        :return: list of missing packet IDs (ints).
        """
        flow_packets_received = self.packet.flow_packets_received
        expected_packet_id = 0
        missing_packets = []

        # TODO(team): Make more efficient based on Nov 9 meeting discussion (?)
        for i in range(len(flow_packets_received)):
            # Check precondition that list is increasing
            if i >= 1:
                assert flow_packets_received[i] > flow_packets_received[i - 1]

            # Increase expected ID until the gap has been covered.
            this_packet_id = flow_packets_received[i]
            while expected_packet_id < this_packet_id:
                missing_packets.append(expected_packet_id)
                expected_packet_id += 1

            expected_packet_id += 1

        return missing_packets

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

        # Mark ACK'd packet as no longer in transit, and successfully
        # received. This will update the window size etc as necessary.
        self.flow.packets_in_transit.remove(self.packet.packet_id)
        self.flow.handle_packet_success(self.packet.packet_id)

        # Check if there are any packets missing in the AckPacket's
        # flow_packets_received (as per selective repeat).
        self.lost_packet_ids = self.find_missing_packets()

    def schedule_new_events(self, main_event_loop):
        """
        Schedule Flow events based on whether a Packet loss occurred (must
        trigger retransmit) or not (fill up window size as much as possible).

        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        # Deal with lost Packets. This involves letting the Flow update its
        # window size and schedule new FlowSendPacketsEvents in its
        # specialized way. NOTE: assuming all losses are gaps.
        for packet_id in self.lost_packet_ids:
            self.flow.handle_packet_loss(packet_id,
                                         PacketLossType.GAP_ACK,
                                         main_event_loop)

        # Even if a Packet loss occurred, we can try to schedule new Packets
        # to send (if there's a big enough window size).
        curr_window_size = len(self.flow.packets_in_transit)
        packets_to_send = []
        while curr_window_size < self.flow.get_window_size():
            new_packet_id = self.flow.get_next_data_packet_id()
            if self.flow.packet_id_exceeds_data(new_packet_id):
                # We are out of packets to send. Send Complete Event.
                flow_complete = FlowCompleteEvent(self.flow)
                main_event_loop.schedule_event_with_delay(flow_complete, 0.0)
                return

            new_packet = DataPacket(packet_id=new_packet_id,
                                    flow_id=self.flow.flow_id,
                                    source_id=self.flow.source_addr,
                                    dest_id=self.flow.dest_addr,
                                    start_time_sec=
                                    main_event_loop.global_clock_sec)
            packets_to_send.append(new_packet)

        if len(packets_to_send) > 0:
            flow_send_event = FlowSendPacketsEvent(self.flow, packets_to_send)
            main_event_loop.schedule_event_with_delay(flow_send_event, 0.0)


class FlowCompleteEvent(Event):
    """
    Triggered when ACK'd packet's ID exceeds data size, i.e. we have no more
    packets to send.
    """
    def __init__(self, flow):
        super(FlowCompleteEvent, self).__init__()
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
