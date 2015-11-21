"""
This module holds the Link class, the LinkBuffer class, the LinkBufferElement
class, and various Link-related Events.
"""

import logging

import numpy as np

from event import Event
from router import Router, RouterReceivedPacketEvent
from packet import RouterPacket

logger = logging.getLogger(__name__)


class LinkBuffer(object):
    """
    Representation of a Link's FIFO buffer.
    """

    """
    The maximum number of Packets to average over in computing the queuing
    delay.
    """
    NUM_ELEMS_AVE_Q_DEL = 30

    # TODO(team): Parameters related to link congestion, so we can have dynamic
    # routing table updates.
    # TODO(yubo): packet_exemption_times deque

    def __init__(self, max_buffer_size_bits=None, queue=None):
        """
        :ivar int max_buffer_size_bits: maximum buffer size in bits.
        :ivar Queue queue: a FIFO queue of LinkBufferElements. This is
        initialized in network_topology.py.
        :ivar int curr_buffer_size_bits: current buffer size in bits
        :ivar deque queuing_delays: a deque of floats representing how long the
        last NUM_ELEMS_AVE_Q_DEL elements were in the buffer. This is
        initialized in network_topology.py.
        """
        self.max_buffer_size_bits = max_buffer_size_bits
        self.queue = queue
        self.curr_buffer_size_bits = 0
        self.queuing_delays = None

    def __repr__(self):
        return str(self.__dict__)

    def remaining_size_bits(self):
        """
        Returns remaining size of buffer in bits. Used by push()
        :return: remaining buffer size in bits
        """
        return self.max_buffer_size_bits - self.curr_buffer_size_bits

    def get_num_packets(self):
        """
        :return: The number of Packets in the queue
        """
        return self.queue.qsize()

    def push(self, packet, dest_dev, global_clock_sec):
        """
        Pushes packet onto LinkBuffer going towards packet.dest_id

        :param Packet packet: Packet to push
        :param Device dest_dev: destination Device of packet
        :param: global_clock_sec: the current time (in sec)
        :return: True if pushed, False if not
        """
        # If we have a RouterPacket or if there is sufficient capacity, push
        if isinstance(packet, RouterPacket) or \
                self.remaining_size_bits() > packet.size_bits:
            self.curr_buffer_size_bits += packet.size_bits
            self.queue.put(LinkBufferElement(packet, dest_dev,
                                             global_clock_sec))
            return True
        else:
            return False # failed to push

    def pop(self, global_clock_sec):
        """
        Pops off top LinkBufferElement and updates metadata. This includes
        updating the latest queuing delay.
        :param: global_clock_sec: the current time (in sec)
        :return: top LinkBufferElement
        """
        buff_elem = self.queue.get()
        self.curr_buffer_size_bits -= buff_elem.packet.size_bits

        # Add this queuing delay to the left of the deque, and remove any old
        # ones from the right.
        this_q_del = global_clock_sec - buff_elem.entry_time
        assert this_q_del >= 0.0
        self.queuing_delays.appendleft(this_q_del)
        while len(self.queuing_delays) > LinkBuffer.NUM_ELEMS_AVE_Q_DEL:
            self.queuing_delays.pop()

        return buff_elem

    def get_average_q_del_sec(self):
        """
        Computes the average queuing delay, using the most recent
        NUM_ELEMS_AVE_Q_DEL Packets' delays.
        """
        # Do not compute an average if fewer than NUM_ELEMS_AVE_Q_DEL Packets
        # have queued at this Link.
        if len(self.queuing_delays) < LinkBuffer.NUM_ELEMS_AVE_Q_DEL:
            return 0.0

        return np.mean(self.queuing_delays)


class LinkBufferElement(object):
    """
    Wrapper class containing a Packet, destination Device on Link
    and time of entry to buffer
    """
    def __init__(self, packet, dest_dev, entry_time):
        """
        :ivar Packet packet packet in buffer element
        :ivar Device dest_dev: destination of packet
        :ivar entry_time time packet entering buffer
        """
        self.packet = packet
        self.dest_dev = dest_dev
        self.entry_time = entry_time

    def __repr__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.__dict__ == other.__dict__


class Link(object):
    """
    Representation of a half-duplex link.

    Note: in the input JSON, the addresses at the ends of the Link will be
    specified, but not the Devices themselves (since those are references).
    """

    def __init__(self, name=None, end_1_addr=None, end_2_addr=None, end_1_device=None,
            end_2_device=None, link_buffer=LinkBuffer(), static_delay_sec=None,
            capacity_bps=None, busy=False):
        """
        :ivar str name: name of a Link
        :ivar string end_1_addr: address of Device on one end (e.g. "H1").
        :ivar string end_2_addr: address of Device on other end (e.g. "H2").
        :ivar Device end_1_device: actual Device on one end.
        :ivar Device end_2_device: actual Device on the other end.
        :ivar LinkBuffer link_buffer: the link's buffer.
        :ivar float static_delay_sec: link propagation delay in seconds
        :ivar float capacity_bps: max link capacity in bits per second.
        :ivar boolean busy: whether the Link is being used for transmission
        at the moment.
        """
        self.name = name
        self.end_1_addr = end_1_addr
        self.end_2_addr = end_2_addr
        self.end_1_device = end_1_device
        self.end_2_device = end_2_device
        self.link_buffer = link_buffer
        self.static_delay_sec = static_delay_sec
        self.capacity_bps = capacity_bps
        self.busy = busy

    def __repr__(self):
        return str(self.__dict__)

    def __hash__(self):
        return hash(self.end_1_addr + self.end_2_addr)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def get_link_cost(self):
        """
        Returns link cost. This is the sum of the propagation delay and the
        average queuing delay over the last few packets. Transmission delay
        is ignored.
        :return: float of link delay time in seconds
        """
        return self.static_delay_sec + self.link_buffer.get_average_q_del_sec()

    def get_other_end(self, one_end):
        """
        :param Device one_end: The Device on one end of the Link.
        :return: Device on the other end of the Link.
        :except: ValueError if one_end is not one of the Link ends.
        """
        if self.end_1_device == one_end:
            return self.end_2_device
        elif self.end_2_device == one_end:
            return self.end_1_device
        else:
            raise ValueError("Device " + one_end.address + " was not one of "
                             "the ends in Link " + str(self))

    def push(self, packet, dest_dev, global_clock_sec):
        """
        Pushes packet onto own LinkBuffer

        :param Packet packet: Packet to push
        :param Device dest_dev: destination Device of packet
        :param global_clock_sec: store when packet pushed
        :return: True if pushed, False if not
        """
        return self.link_buffer.push(packet, dest_dev, global_clock_sec)


class LinkSendEvent(Event):
    """
    This Event pops a buffer element and sends it with the appropriate
    transmission and propagation delays. It then schedules another check on
    the link status, for one transmission delay later.
    """

    def __init__(self, link):
        """
        :ivar link: link that must send its next packet
        :ivar buffer_elem: temporary variable containing LinkBufferElement to
            send
        """
        Event.__init__(self)
        self.link = link
        self.buffer_elem = None

    def run(self, main_event_loop, statistics):
        """
        runs by popping off top packet
        :param MainEventLoop main_event_loop: event loop for global timing
        :param Statistics statistics: the Statistics to update
        """
        # sanity check
        if self.link.link_buffer.get_num_packets() == 0:
            logger.warning("LinkSendEvent while Link empty!")
            return

        # now pop
        self.buffer_elem = self.link.link_buffer.pop(
            main_event_loop.global_clock_sec)

        # update statistics only if not RouterPacket
        if not isinstance(self.buffer_elem.packet, RouterPacket):
            statistics.link_packet_transmitted(
                self.link,self.buffer_elem.packet,
                main_event_loop.global_clock_sec)

    def schedule_new_events(self, main_event_loop):
        """
        Schedules new Events. This is called immediately after run().
        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        # Schedule a *ReceivedPacketEvent with propagation + transmission
        # delay, depending on whether Host or Router
        propagation_delay = self.link.static_delay_sec
        transmission_delay = self.buffer_elem.packet.size_bits / \
                             float(self.link.capacity_bps)

        if isinstance(self.buffer_elem.dest_dev, Router):
            main_event_loop.schedule_event_with_delay(
                    RouterReceivedPacketEvent(router=self.buffer_elem.dest_dev,
                                              packet=self.buffer_elem.packet),
                    propagation_delay + transmission_delay)
            logger.debug("Link used at time %f: %s",
                         main_event_loop.global_clock_sec, self.link.name)
        else:
            from host import Host, HostReceivedPacketEvent
            assert isinstance(self.buffer_elem.dest_dev, Host)
            main_event_loop.schedule_event_with_delay(
                    HostReceivedPacketEvent(host=self.buffer_elem.dest_dev,
                                            packet=self.buffer_elem.packet),
                    propagation_delay + transmission_delay)

        # Check on the buffer after one transmission delay, to see if
        # there're more Packets in the buffer or if the Link can be made free.
        assert self.link.busy
        check_stat_ev = CheckLinkStatusEvent(link=self.link)
        main_event_loop.schedule_event_with_delay(check_stat_ev,
                                                  transmission_delay)


class CheckLinkStatusEvent(Event):
    """
    This Event checks if the Link's buffer is empty or not. If it is not
    empty, a new LinkSendEvent is scheduled. Otherwise, the Link is marked as
    not busy.
    """

    def __init__(self, link):
        """
        :ivar link: The Link to check.
        """
        super(CheckLinkStatusEvent, self).__init__()
        self.link = link

    def run(self, main_event_loop, statistics):
        """
        Marks Link as non-busy if buffer is still empty.
        :param MainEventLoop main_event_loop: event loop
        :param Statistics statistics: statistics
        """
        if self.link.link_buffer.get_num_packets() == 0:
            self.link.busy = False

    def schedule_new_events(self, main_event_loop):
        """
        If the buffer is not empty, then schedule a LinkSendEvent immediately.
        :param MainEventLoop main_event_loop: event loop.
        """
        if self.link.link_buffer.get_num_packets() != 0:
            main_event_loop.schedule_event_with_delay(
                LinkSendEvent(self.link), 0.0)
            self.link.busy = True


class DeviceToLinkEvent(Event):
    """
    Event representing a packet going from one of two Devices connected to Link
    to Link's LinkBuffer
    """

    def __init__(self, packet, link, dest_dev):
        """
        :ivar packet: packet arriving at Link
        :ivar link: link that packet is arriving at
        :ivar dest_dev: destination Device of the packet pushed onto link
        """
        Event.__init__(self)

        # Sanity check
        assert link.end_1_device == dest_dev or link.end_2_device == dest_dev
        self.packet = packet
        self.link = link
        self.dest_dev = dest_dev

    def run(self, main_event_loop, statistics):
        """
        DeviceToLinkEvent run's by trying to push the packet onto link's buffer
        :param MainEventLoop main_event_loop: event loop for global timing
        :param Statistics statistics: the Statistics to update
        """
        # if successfully pushed
        if self.link.push(self.packet, self.dest_dev,
                          main_event_loop.global_clock_sec):
            statistics.link_buffer_occ_change(self.link,
                                              main_event_loop.global_clock_sec)
        else:
            statistics.link_packet_loss(self.link,
                                        main_event_loop.global_clock_sec)

    def schedule_new_events(self, main_event_loop):
        """
        Schedules new LinkSendEvent iff Link was not already busy/already has
        LinkSendEvent in queue
        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        # Only schedule new event if link not busy. Note that dropped packet
        # will be no-op under this, since link would have to be full and
        # definitely be busy if a packet were dropped.
        if not self.link.busy:
            main_event_loop.schedule_event_with_delay(
                LinkSendEvent(self.link), 0.0)
            self.link.busy = True