"""
Module for the abstract Flow class, its subclasses (which implement various
TCP algorithms), and Flow-related Events.
"""

from abc import ABCMeta, abstractmethod
import copy
import logging
from Queue import Queue

import numpy as np

from common import *
from event import Event
from link import DeviceToLinkEvent
from packet import AckPacket, DataPacket

logger = logging.getLogger(__name__)


class PacketLossType(object):
    """
    An enum for describing different kinds of Packet losses, as detected by
    the Flow that sent the Packet.
    """
    # AckPacket not received after FLOW_TIMEOUT_SEC seconds.
    TIMEOUT = 0

    # Gap in AckPacket's selective repeat data
    GAP_ACK = 1


class FlowState(object):
    """
    An enum for describing different kinds of Flow states. This is currently
    only used by TCP Reno.
    """
    SLOW_START = 0
    CONGESTION_AVOIDANCE = 1
    FAST_RETRANS_AND_RECO = 2  # Reno only


class Flow(object):
    """
    Representation of general (abstract) Flow. Subclasses implement specific
    TCP algorithms.
    """
    __metaclass__ = ABCMeta

    def __init__(self, flow_id, source_addr, dest_addr,
                 data_size_bits, start_time_sec):
        """
        :ivar string flow_id: unique string ID for this Flow.
        :ivar string source_addr: address of source Host.
        :ivar string dest_addr: address of destination Host.
        :ivar Host source: source Host.
        :ivar Host dest: dest Host.
        :ivar float window_size_packets: The maximum number of packets that
        can be in transit at a given time.
        :ivar set<int> packets_in_transit: set of packet IDs that are either
        currently in transit, or *scheduled* to be in transit.
        :ivar list packet_rtts: list of (packet_id, rtt) tuples that stores
        the RTT for each Packet that completed a round trip.
        :ivar int data_size_bits: total amount of data to transmit in bits.
        Assumed to be a multiple of the DataPacket size.
        :ivar float start_time_sec: start time relative to global clock.
        :ivar int max_packet_id_sent: the maximum DataPacket ID that has been
        sent (might not have been ACK'd yet).
        :ivar set<int> gap_retrans_packets: a set of DataPacket IDs that have
        been retransmitted (or buffered to retransmit) following an ACK gap (or
        multiple ACK gaps, as in Reno). This is used to make sure we don't
        retransmit the same packet ID multiple times after many gaps.
        :ivar dict num_timeouts_pending: a map from Packet ID (int) to the
        number of timeouts that are pending for this Packet (if any). This is
        used to make sure that, if there are (e.g.) 2 timeouts pending for a
        Packet, we only respond to the later one. Earlier one corresponds to
        a lost packet that was then retransmitted.
        """
        self.flow_id = flow_id
        self.source_addr = source_addr
        self.dest_addr = dest_addr
        self.source = None  # initialized later in network_topology.py
        self.dest = None  # initialized later in network_topology.py
        self.window_size_packets = float(INITIAL_WINDOW_SIZE_PACKETS)
        self.packets_in_transit = set()
        self.packet_rtts = list()
        self.data_size_bits = data_size_bits
        self.start_time_sec = start_time_sec
        self.max_packet_id_sent = -1  # so first ID sent is 0.
        self.gap_retrans_packets = set()
        self.num_timeouts_pending = dict()

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
        :return: (float) current window size in packets
        """
        return self.window_size_packets

    def get_next_data_packet_id(self, peek=False):
        """
        Helper function to get the next DataPacket ID to *send*.

        :param bool peek: If True, none of the internal metadata of the Flow
        (e.g. self.max_packet_id_sent) is updated.
        :return: int (next DataPacket's ID)
        """
        next_packet_id = self.max_packet_id_sent + 1

        # Only update the max packet ID sent if the new Packet ID doesn't
        # exceed the data size (and we're not peeking).
        if not peek and not self.packet_id_exceeds_data(next_packet_id):
            self.max_packet_id_sent = max(self.max_packet_id_sent,
                                          next_packet_id)

        return next_packet_id

    def record_pending_timeout(self, packet_id):
        """
        Records that there is a new pending timeout for the given Packet.
        :param int packet_id: ID of Packet that is being sent.
        """
        self.num_timeouts_pending[packet_id] = \
            self.num_timeouts_pending.get(packet_id, 0) + 1

    def record_received_timeout(self, packet_id):
        """
        Records that a timeout was received for the given Packet, and returns
        the old number of pending timeouts. If no timeouts were pending,
        0 is returned.
        :param int packet_id: ID of Packet received.
        :return: The old number of pending timeouts (int), before this call.
        """
        if packet_id not in self.num_timeouts_pending:
            return 0
        else:
            old_pending_timeouts = self.num_timeouts_pending[packet_id]
            self.num_timeouts_pending[packet_id] -= 1
            return old_pending_timeouts

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
        logger.debug("Flow %s lost packet %d via PacketLossType %d",
                     self.flow_id, packet_id, loss_type)

    @abstractmethod
    def handle_packet_success(self, packet, statistics, curr_time):
        """
        A handler for dealing with packets that successfully completed a
        round trip. This will adjust window sizes and make other state
        changes, depending on the TCP congestion algorithm. It will also
        update common metadata and statistics.

        The sending of additional Packets (e.g. if the window size is grown)
        must be handled elsewhere, since this can be subclass-dependent.
        :param Packet packet: The AckPacket that completed a round trip.
        :param Statistics statistics: The Statistics to update.
        :param float curr_time: The current simulation time (in seconds).
        """
        assert isinstance(packet, AckPacket)

        # Update RTTs
        sent_time = packet.data_packet_start_time_sec
        curr_rtt = curr_time - sent_time
        self.packet_rtts.append((packet.packet_id, curr_rtt))

        # All Flows need to properly update state variables related to
        # transiting/retransmitted packets.
        self.packets_in_transit.remove(packet.packet_id)
        if packet.packet_id in self.gap_retrans_packets:
            self.gap_retrans_packets.remove(packet.packet_id)

        # No longer need to do anything on timeouts for this Packet.
        del self.num_timeouts_pending[packet.packet_id]

        # All Flows should record these statistics.
        statistics.flow_packet_received(flow=self, ack_packet=packet,
                                        curr_time=curr_time)

    def retransmit(self, packet_id, main_event_loop):
        """
        Retransmits the given Packet by scheduling a FlowSendPacketsEvent.
        This will only be done if the Packet is already currently in transit
        (otherwise retransmitting makes no sense).
        :param int packet_id: ID of Packet to retransmit.
        :param MainEventLoop main_event_loop: event loop.
        """
        assert packet_id in self.packets_in_transit
        this_packet = DataPacket(
            packet_id=packet_id, flow_id=self.flow_id,
            source_id=self.source_addr, dest_id=self.dest_addr,
            start_time_sec=main_event_loop.global_clock_sec)
        flow_send_event = FlowSendPacketsEvent(self, [this_packet])
        main_event_loop.schedule_event_with_delay(flow_send_event, 0.0)
        logger.debug("Flow %s successfully scheduled a retransmit of "
                     "packet %d.", self.flow_id, packet_id)

    def send_packets_to_fill_window(self, main_event_loop):
        """
        A helper function that sends enough DataPackets to fill the current
        window of the TCP algorithm.
        :param MainEventLoop main_event_loop: event loop for scheduling Events.
        """
        curr_window_size = len(self.packets_in_transit)
        packets_to_send = []
        while curr_window_size < int(self.window_size_packets):
            new_packet_id = self.get_next_data_packet_id()
            if self.packet_id_exceeds_data(new_packet_id):
                # We are out of Packets to send. Send what's already there.
                break

            new_packet = DataPacket(packet_id=new_packet_id,
                                    flow_id=self.flow_id,
                                    source_id=self.source_addr,
                                    dest_id=self.dest_addr,
                                    start_time_sec=
                                    main_event_loop.global_clock_sec)
            packets_to_send.append(new_packet)
            curr_window_size += 1

        if len(packets_to_send) > 0:
            flow_send_event = FlowSendPacketsEvent(self, packets_to_send)
            main_event_loop.schedule_event_with_delay(flow_send_event, 0.0)

    def __repr__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.flow_id == other.flow_id


class FlowDummy(Flow):
    """
    A dummy Flow implementation, for testing only. This just maintains a
    window size of 1 packet. Successes and losses do not change the window
    size. Losses result in retransmits.
    """

    def __init__(self, flow_id, source_addr, dest_addr,
                 data_size_bits, start_time_sec):
        super(FlowDummy, self).__init__(flow_id=flow_id,
                                        source_addr=source_addr,
                                        dest_addr=dest_addr,
                                        data_size_bits=data_size_bits,
                                        start_time_sec=start_time_sec)

    def handle_packet_success(self, packet, statistics, curr_time):
        """
        Update metadata and stats, but do nothing to window size.
        :param Packet packet: The Packet received.
        :param Statistics statistics: Statistics to update.
        :param float curr_time: current simulation time in seconds.
        """
        super(FlowDummy, self).handle_packet_success(packet, statistics,
                                                     curr_time)

    def handle_packet_loss(self, packet_id, loss_type, main_event_loop):
        """
        Update metadata and retransmit the packet if possible. Do not change
        window size.
        :param int packet_id: the lost Packet's id.
        :param PacketLossType loss_type: the kind of loss that occurred.
        :param MainEventLoop main_event_loop: event loop.
        """
        super(FlowDummy, self).handle_packet_loss(packet_id, loss_type,
                                                  main_event_loop)
        if loss_type == PacketLossType.GAP_ACK:
            self.gap_retrans_packets.add(packet_id)

        self.retransmit(packet_id, main_event_loop)


class FlowReno(Flow):
    """
    TCP Reno implementation for Flows. Window sizes are updated on receipt of
    ACKs or timeouts. Fast retransmit / fast recovery (FR/FR) is also
    implemented.

    See http://goo.gl/ctps5S and
    http://courses.cms.caltech.edu/cs143/Slides/Low-201108-TCP-Cambridge.pdf
    for more details on Reno.
    """

    """
    Number of ACK gaps required for a particular packet before Reno enters
    the FR/FR state. The value 3 is commonly used for this.
    """
    ACK_GAPS_FR_FR = 3

    def __init__(self, flow_id, source_addr, dest_addr,
                 data_size_bits, start_time_sec,
                 initial_ss_thresh=TCP_INITIAL_SS_THRESH):
        """
        Additional ivars (not in Flow):
        :ivar FlowState flow_state: the current state of the Flow.
        :ivar float ss_thresh: threshold number of packets required before
        exiting slow start (SS). Note that, in Reno, SS is mostly entered
        post-timeouts and at the beginning, since FR/FR exits to CA.
        :ivar dict packet_id_to_ack_gaps: A map from Packet ID (int) to the
        number of ACK gaps (from selective repeat; also int) that have been
        found to contain this Packet.

        Note that gap_retrans_packets is populated when 3 AckPackets containing
        the same ACK gap (e.g. 3 packets saying packet "4" is missing) are
        received.
        """
        super(FlowReno, self).__init__(flow_id=flow_id, source_addr=source_addr,
                                       dest_addr=dest_addr,
                                       data_size_bits=data_size_bits,
                                       start_time_sec=start_time_sec)
        assert initial_ss_thresh > 0
        self.ss_thresh = initial_ss_thresh
        self.flow_state = FlowState.SLOW_START
        self.packet_id_to_ack_gaps = dict()

    def update_window_size_and_state(self):
        """
        Updates window size, SS threshold, and flow state after receiving an
        ACK, based on current state.

        Precondition: an ACK was received indicating successes, and this ACK
        did not contain any gaps (i.e. packet.loss_occurred was False).
        """
        if self.flow_state == FlowState.FAST_RETRANS_AND_RECO:
            # See if we can leave FR/FR. For this to be the case, there can
            # no longer be Packets that were retransmitted after 3 ACK gaps.
            if len(self.gap_retrans_packets) == 0:
                # FR/FR always exits directly to CA in Reno, and resets to
                # the slow start threshold (window deflation).
                self.flow_state = FlowState.CONGESTION_AVOIDANCE
                self.window_size_packets = self.ss_thresh
            else:
                # Fast recovery
                self.window_size_packets += 1

        elif self.flow_state == FlowState.SLOW_START:
            self.window_size_packets += 1

            # Enter CA if SS threshold is exceeded.
            if self.window_size_packets >= self.ss_thresh:
                self.flow_state = FlowState.CONGESTION_AVOIDANCE

        elif self.flow_state == FlowState.CONGESTION_AVOIDANCE:
            self.window_size_packets += 1.0 / self.window_size_packets
        else:
            raise ValueError("Invalid flow state for Reno: %d.",
                             self.flow_state)

    def handle_packet_success(self, packet, statistics, curr_time):
        """
        Handler function called after a successful ACKPacket. This updates
        metadata and then updates the window size based on the flow state.
        This is also where we can exit SS or FR/FR.

        Note that this function must be called on the AckPackets successfully
        received *before* the losses described in those Packets are dealt with.
        See FlowReceivedAckEvent. Also, this function does not itself try to
        fill a window size.
        """
        super(FlowReno, self).handle_packet_success(packet, statistics,
                                                    curr_time)

        # logger.debug("ACK for Packet %d received. Initial flow state: %d",
        #              packet.packet_id, self.flow_state)

        if packet.packet_id in self.packet_id_to_ack_gaps:
            del self.packet_id_to_ack_gaps[packet.packet_id]

        # If the packets indicate that a loss occurred, do not update the
        # window size.
        old_window_size = self.window_size_packets
        if not packet.loss_occurred:
            self.update_window_size_and_state()

        # logger.debug("Old window size: %f. New window size: %f.",
        #              old_window_size, self.window_size_packets)
        # logger.debug("New flow state: %d.", self.flow_state)

    def handle_packet_loss(self, packet_id, loss_type, main_event_loop):
        """
        Handler function for dealing with packet losses (timeouts / ACK
        gaps). Timeouts immediately result in retransmits. But ACK gaps only
        result in retransmits if more than 3 have been received for that
        Packet. This will trigger FR/FR.
        """
        super(FlowReno, self).handle_packet_loss(packet_id, loss_type,
                                                 main_event_loop)

        logger.debug("Initial flow state: %d.", self.flow_state)

        if loss_type == PacketLossType.TIMEOUT:
            # Timeouts same as Tahoe: enter SS and update SS threshold. Also,
            # always retransmit.
            self.ss_thresh = self.window_size_packets / 2.0
            self.window_size_packets = 1.0
            self.flow_state = FlowState.SLOW_START
            self.retransmit(packet_id, main_event_loop)

            logger.debug("Entered SS due to timeout. New ss_thresh: %f. New "
                         "window size: %f.", self.ss_thresh,
                         self.window_size_packets)
        elif loss_type == PacketLossType.GAP_ACK:
            # Update the packet_id_to_ack_gaps map and enter FR/FR if needed.
            num_ack_gaps = \
                self.packet_id_to_ack_gaps.get(packet_id, 0) + 1
            self.packet_id_to_ack_gaps[packet_id] = num_ack_gaps

            # Do not redo the conditions that lead to FR/FR if we've already
            # marked this packet as "lost" (i.e. >= 3 ACK gaps) and
            # retransmitted it. Do this by checking gap_retrans_packets.
            if num_ack_gaps >= FlowReno.ACK_GAPS_FR_FR \
                    and packet_id not in self.gap_retrans_packets:
                # Sanity check that is currently true.
                assert num_ack_gaps == FlowReno.ACK_GAPS_FR_FR

                self.flow_state = FlowState.FAST_RETRANS_AND_RECO
                self.ss_thresh = max(self.window_size_packets / 2.0, 2.0)

                # Fast retransmit before changing window size.
                self.gap_retrans_packets.add(packet_id)
                self.retransmit(packet_id, main_event_loop)
                self.window_size_packets = self.ss_thresh + num_ack_gaps

                logger.debug("Entered FR/FR. SS thresh: %f. Window size: %f.",
                             self.ss_thresh, self.window_size_packets)
            else:
                # Do not do anything to update window size in this case.
                # logger.debug("Did not enter FR/FR after ACK gap. Number of "
                #              "ACK gaps for packet was %d. Packet already "
                #              "retransmitted: %r.", num_ack_gaps,
                #              packet_id in self.gap_retrans_packets)
                pass


class FlowFast(Flow):
    """
    TCP FAST implementation for Flows. Note that window sizes in FAST are
    only updated periodically, and packet successes/losses are just used to
    track statistics.

    See http://netlab.caltech.edu/publications/FAST-ToN-final-060209-2007.pdf
    for more details.
    """

    def __init__(self, flow_id, source_addr, dest_addr,
                 data_size_bits, start_time_sec,
                 alpha=TCP_FAST_DEFAULT_ALPHA, gamma=TCP_FAST_DEFAULT_GAMMA,
                 num_packets_ave_for_rtt=TCP_NUM_PACKETS_AVE_FOR_RTT):
        """
        Additional ivars (not in Flow):
        :ivar float alpha: smoothing parameter for baseRTT/RTT updates (see
        paper).
        :ivar float gamma: smoothing parameter for window update (see paper).
        :ivar float base_rtt: The minimum RTT encountered ever, in seconds.
        :ivar int num_packets_ave_for_rtt: The max number of packets to
        average in computing the average RTT.
        """
        super(FlowFast, self).__init__(flow_id=flow_id, source_addr=source_addr,
                                       dest_addr=dest_addr,
                                       data_size_bits=data_size_bits,
                                       start_time_sec=start_time_sec)
        self.alpha = alpha
        self.gamma = gamma
        self.base_rtt = None  # will be initialized after first ACKs received
        self.num_packets_ave_for_rtt = num_packets_ave_for_rtt

    def handle_packet_success(self, packet, statistics, curr_time):
        """
        Updates Flow metadata and statistics upon receipt of an AckPacket,
        and also updates the minimum RTT seen so far. No window size updates.
        """
        super(FlowFast, self).handle_packet_success(packet, statistics,
                                                    curr_time)

        packet_rtt = curr_time - packet.data_packet_start_time_sec
        if self.base_rtt is None:
            self.base_rtt = packet_rtt
        else:
            self.base_rtt = min(self.base_rtt, packet_rtt)

    def handle_packet_loss(self, packet_id, loss_type, main_event_loop):
        """
        A handler function that is called after a packet loss, which can
        either be a timeout or a single ACK indicating that a given packet is
        missing.

        In the case of TCP FAST, no window size updates happen here. For
        timeouts, the packet is always retransmitted. For ACK gaps, we only
        retransmit the packet if we haven't already retransmitted it due to a
        gap before. This deals with cases where multiple ACKs are returned
        with the same gap.
        """
        super(FlowFast, self).handle_packet_loss(packet_id, loss_type,
                                                 main_event_loop)

        if loss_type == PacketLossType.TIMEOUT:
            # Always retransmit if possible in case of timeouts.
            logger.debug("Flow %s retransmitting packet %d due to timeout.",
                         self.flow_id, packet_id)
            self.retransmit(packet_id, main_event_loop)
        elif loss_type == PacketLossType.GAP_ACK:
            # Check if Packet ID has been retransmitted due to GAP_ACK before.
            if packet_id not in self.gap_retrans_packets:
                logger.debug("Flow %s attempted to retransmit packet %d due to "
                             "GAP_ACK.", self.flow_id, packet_id)
                self.retransmit(packet_id, main_event_loop)
                self.gap_retrans_packets.add(packet_id)
            else:
                logger.debug("Flow %s did not attempt to retransmit packet %d "
                             "since it had already been retransmitted due to "
                             "GAP_ACK before.", self.flow_id, packet_id)

    def handle_periodic_interrupt(self):
        """
        Respond to TCP FAST's periodic interrupts. This is where the window
        size is actually updated. But sending packets to fill the new window
        must occur elsewhere.
        """
        # If no packets successfully ACK'd, do not update the window size.
        if len(self.packet_rtts) == 0:
            return

        # Calculate average_rtt over (at most) the last num_packets_ave_for_rtt
        # packets. RTTs are stored in (packet_id, rtt) form in packet_rtts.
        num_packets_to_ave = min(self.num_packets_ave_for_rtt,
                                 len(self.packet_rtts))
        last_packet_rtt_elems = self.packet_rtts[-num_packets_to_ave:]
        average_rtt = np.mean([elem[1] for elem in last_packet_rtt_elems])

        # The formula for the new window size comes from the TCP FAST paper,
        # and accounts for a "slow start"-like phase via the min.
        old_window_size = self.window_size_packets
        new_window_size = min(2.0 * old_window_size,
                              (1.0 - self.gamma) * old_window_size
                              + self.gamma * (self.base_rtt / average_rtt *
                                              old_window_size +
                                              self.alpha))
        self.window_size_packets = new_window_size

        # logger.debug("Flow %s updated window size from %f pkts to %f pkts "
        #              "during periodic TCP FAST update.", self.flow_id,
        #              old_window_size, new_window_size)


class InitiateFlowEvent(Event):
    """
    A one-time Event called to set up the Flow at a given timestamp.
    """
    def __init__(self, flow):
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
        max_window_size = int(self.flow.get_window_size())
        while len(packet_ids) < max_window_size:
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

    def schedule_new_events(self, main_event_loop, statistics):
        """
        Schedule a FlowSendPacketsEvent immediately, with the list of packets
        to send. If this is a TCP algorithm using periodic repeats,
        also schedule a PeriodicFlowInterrupt.

        :param Statistics statistics: the Statistics to update
        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        flow_send_event = FlowSendPacketsEvent(self.flow,
                                               self.packets_to_send)
        main_event_loop.schedule_event_with_delay(flow_send_event, 0.0)

        if isinstance(self.flow, FlowFast):
            period = TCP_FAST_UPDATE_PERIOD_SEC
            periodic_interrupt = PeriodicFlowInterrupt(flow=self.flow,
                                                       time_period_sec=period)
            main_event_loop.schedule_event_with_delay(periodic_interrupt,
                                                      period)


class PeriodicFlowInterrupt(Event):
    """
    A periodic interrupt Event that is used to update some TCP flows'
    internal parameters. Currently, this is only used with TCP FAST. The
    Flows that can handle periodic interrupts should implement a
    handle_periodic_interrupt() function.

    This Event will always call itself again and again once it is done
    running; it is up to the MainEventLoop to stop the interrupts when the
    Flow is complete.
    """

    def __init__(self, flow, time_period_sec):
        """
        :ivar Flow flow: The Flow whose parameters we periodically update.
        :ivar float time_period_sec: How often (sec) this event will occur.
        :ivar float old_window_size: the old window size (in Packets).
        """
        super(PeriodicFlowInterrupt, self).__init__()
        assert isinstance(flow, FlowFast)
        self.flow = flow
        self.time_period_sec = time_period_sec
        self.old_window_size = None

    def run(self, main_event_loop, statistics):
        """
        Stores old window size and handles periodic interrupt (which alters
        window size based on congestion).
        :param MainEventLoop main_event_loop: main loop.
        :param Statistics statistics: the Statistics to update.
        """
        self.old_window_size = self.flow.get_window_size()
        self.flow.handle_periodic_interrupt()
        statistics.flow_window_size_update(
            flow=self.flow, curr_time=main_event_loop.global_clock_sec)

    def schedule_new_events(self, main_event_loop, statistics):
        """
        Schedules a follow-up interrupt. Also schedule additional packet
        sending if needed, in case the window size has grown.
        :param Statistics statistics: the Statistics to update
        :param MainEventLoop main_event_loop: main loop.
        """
        periodic_interrupt = PeriodicFlowInterrupt(
            flow=self.flow, time_period_sec=self.time_period_sec)
        main_event_loop.schedule_event_with_delay(periodic_interrupt,
                                                  self.time_period_sec)

        # Schedule additional packets as needed, to fill in the window size
        # (if it has grown).
        new_window_size = self.flow.get_window_size()
        if int(new_window_size) > int(self.old_window_size):
            self.flow.send_packets_to_fill_window(main_event_loop)


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

        # Keep track of the packets that are being sent but aren't already in
        # transit.
        new_packets_to_send = 0

        # We want packets_in_transit to reflect Packets that are scheduled to
        # be sent as well, to avoid race conditions.
        for curr_packet in self.packets_to_send:
            if curr_packet.packet_id not in self.flow.packets_in_transit:
                new_packets_to_send += 1
            self.flow.packets_in_transit.add(curr_packet.packet_id)

        # Sanity check that packets_in_transit is not too big now. This
        # happens when new packet(s) is/are sent, AND the window size gets
        # exceeded.
        if new_packets_to_send != 0 and \
                len(self.flow.packets_in_transit) > \
                int(self.flow.get_window_size()):
            # This should never happen if timeouts and filling window sizes
            # are being handled properly.
            raise ValueError("The size of packets in transit + scheduled "
                             "is greater than the Flow's window size, "
                             "after new Packets were scheduled to send.")

    def run(self, main_event_loop, statistics):
        """
        Update statistics only.
        :param MainEventLoop main_event_loop: main loop.
        :param Statistics statistics: the Statistics to update.
        """
        for curr_packet in self.packets_to_send:
            assert isinstance(curr_packet, DataPacket)
            statistics.flow_packet_sent(flow=self.flow, data_packet=curr_packet)
            statistics.host_packet_sent(host=self.flow.source,
                                        packet=curr_packet)

    def schedule_new_events(self, main_event_loop, statistics):
        """
        Send DataPackets via DeviceToLinkEvent, and schedule
        FlowTimeoutPacketEvents.

        :param Statistics statistics: the Statistics to update
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
        :ivar Packet packet: the particular packet of this timeout.
        :ivar int old_pending_timeouts: The number of timeouts that were
        pending for this Packet during the run() call. This is used to check
        whether we need to handle packet losses.
        """
        super(FlowTimeoutPacketEvent, self).__init__()
        self.flow = flow
        self.packet = packet
        self.old_pending_timeouts = None

        # Tell the Flow that we have a pending timeout for this Packet.
        flow.record_pending_timeout(packet.packet_id)

    def run(self, main_event_loop, statistics):
        """
        Records a timeout as received, and stores the old number of pending
        timeouts (i.e. the number before this run() call).
        :param MainEventLoop main_event_loop: Event loop.
        :param Statistics statistics: Statistics to update.
        """
        self.old_pending_timeouts = self.flow.record_received_timeout(
            self.packet.packet_id)

    def schedule_new_events(self, main_event_loop, statistics):
        """
        Check if a packet is in transit. If so, retransmit because it might
        be lost.

        :param Statistics statistics: the Statistics to update
        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        # If the particular packet is currently not in transit (i.e. has
        # returned and been ACK'd), then we don't need to do anything here.
        if self.packet.packet_id not in self.flow.packets_in_transit:
            return

        # If there *was* > 1 pending timeout *before* this timeout occurred,
        # that means there will be another timeout for this packet. This
        # means the packet was retransmitted, so we'll respond to the later one.
        if self.old_pending_timeouts > 1:
            assert self.packet.packet_id in self.flow.gap_retrans_packets
            return

        # handle_packet_loss() will schedule additional Events, e.g. packet
        # sends and timeouts.
        self.flow.handle_packet_loss(self.packet.packet_id,
                                     PacketLossType.TIMEOUT,
                                     main_event_loop)
        statistics.flow_window_size_update(
            flow=self.flow, curr_time=main_event_loop.global_clock_sec)


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
        # Check if there are any packets missing in the AckPacket's
        # flow_packets_received (as per selective repeat).
        self.lost_packet_ids = self.find_missing_packets()

        # If packets were lost, we need to include this in Packet metadata so
        # that handle_packet_success() does not increase window sizes
        # incorrectly.
        self.packet.loss_occurred = (len(self.lost_packet_ids) > 0)

        # Update RTTs, mark ACK'd packet as no longer in transit,
        # and successfully received. This will increase the window size etc as
        # necessary (but window size is only increased if no loss occurred).
        self.flow.handle_packet_success(
            packet=self.packet, statistics=statistics,
            curr_time=main_event_loop.global_clock_sec)

        # Mark the change in window size if no packet losses occurred
        # (otherwise, only mark the change after losses are handled).
        if not self.packet.loss_occurred:
            statistics.flow_window_size_update(
                flow=self.flow, curr_time=main_event_loop.global_clock_sec)

    def schedule_new_events(self, main_event_loop, statistics):
        """
        Schedule Flow events based on whether a Packet loss occurred (must
        trigger retransmit) or not (fill up window size as much as possible).
        Also schedule a FlowCompleteEvent if there's no more data to send.

        :param Statistics statistics: the Statistics to update
        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        # If we didn't lose any Packets and no more are in transit, check if
        # we've managed to transmit all of the data needed. (If there are
        # losses, retransmits will be needed, so we cannot mark the Flow as
        # done yet).
        if not self.packet.loss_occurred and \
                len(self.flow.packets_in_transit) == 0:
            # Peek at next Packet ID without updating Flow metadata
            new_packet_id = self.flow.get_next_data_packet_id(peek=True)
            if self.flow.packet_id_exceeds_data(new_packet_id):
                # We are out of packets to send. Send Complete Event.
                flow_complete = FlowCompleteEvent(self.flow)
                main_event_loop.schedule_event_with_delay(flow_complete, 0.0)
                return

        # Deal with lost Packets. This involves letting the Flow update its
        # window size and schedule new FlowSendPacketsEvents in its
        # specialized way. NOTE: assuming all losses are gaps.
        for packet_id in self.lost_packet_ids:
            # logger.debug("Lost packets: %s", self.lost_packet_ids)
            self.flow.handle_packet_loss(packet_id,
                                         PacketLossType.GAP_ACK,
                                         main_event_loop)

        # Only update window size after all losses handled.
        if self.packet.loss_occurred:
            statistics.flow_window_size_update(
                flow=self.flow, curr_time=main_event_loop.global_clock_sec)

        # Even if a Packet loss occurred, we can try to schedule new Packets
        # to send (if there's a big enough window size).
        self.flow.send_packets_to_fill_window(main_event_loop)


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
        logger.info("Flow %s completed at time %f s.", self.flow.flow_id,
                    main_event_loop.global_clock_sec)

    def schedule_new_events(self, main_event_loop, statistics):
        """

        :param Statistics statistics: the Statistics to update
        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        # Do nothing.
        pass
