"""
This module holds the Link class, the LinkBuffer class, the LinkBufferElement
class, and various Link-related Events.
"""

from Queue import Queue
from packet import *
from common import *
from event import *
import logging

logger = logging.getLogger(__name__)



class LinkBuffer(object):
    """
    Representation of a Link's FIFO buffer.
    """

    # TODO(team): Parameters related to link congestion, so we can have dynamic
    # routing table updates.
    # TODO(yubo): packet_exemption_times deque

    def __init__(self, max_buffer_size_bits=None, queue=Queue()):
        """
        :ivar int max_buffer_size_bits: maximum buffer size in bits.
        :ivar Queue queue: a FIFO queue of LinkBufferElements
        :ivar int curr_buffer_size_bits: current buffer size in bits
        """
        self.max_buffer_size_bits = max_buffer_size_bits
        self.queue = queue

    def __repr__(self):
        return str(self.__dict__)

    def remaining(self):
        """
        returns remaining size in buffer in bits

        not strictly necessary, push() will check remaining() condition
        :return: remaining buffer size in bits
        """
        return self.max_buffer_size_bits - self.curr_buffer_size_bits

    def push(self, packet, global_clock_sec):
        """
        Pushes packet onto LinkBuffer going towards packet.dest_id

        :param Packet packet: Packet to push
        :return: True if pushed, False if not
        """
        if isinstance(packet, RouterPacket):
            # always push RouterPacket
            self.queue.put(LinkBufferElement(\
                    packet, packet.dest_id, global_clock_sec))
            self.curr_buffer_size_bits += ROUTER_PACKET_SIZE_BITS
            return True

        elif isinstance(packet, DataPacket) and \
                self.remaining() > DATA_PACKET_SIZE_BITS:
            # if DataPacket & has room
            self.curr_buffer_size_bits += DATA_PACKET_SIZE_BITS
            self.queue.put(LinkBufferElement(\
                    packet, packet.dest_id, global_clock_sec))
            return True

        elif isinstance(packet, AckPacket) and \
                self.remaining() > ACK_PACKET_SIZE_BITS:
            # if AckPacket & has room
            self.curr_buffer_size_bits += ACK_PACKET_SIZE_BITS
            self.queue.put(LinkBufferElement(packet, packet.dest_id,\
                    global_clock_sec))
            return True
        else:
            return False # failed to push

    def pop(self):
        """
        pops off top LinkBufferElement and returns it
        :return: top LinkBufferElement
        """
        return self.queue.get()



class LinkBufferElement(object):
    """
    Wrapper class containing a Packet and which Device address it's going to
    (i.e. the direction).
    """
    def __init__(self, packet, entry_time):
        """
        :ivar Packet packet packet in buffer element
        :ivar entry_time current time that packet is being pushed onto queue
        """
        self.packet = packet
        self.entry_time = entry_time

    def __repr__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.__dict__ == other.__dict__

    def get_packet(self):
        """
        return packet of LinkBufferElement
        :return Packet packet that is in the buffer element
        """
        return self.packet

    def get_dest(self):
        """
        return destination of LinkBufferElement
        :return string destination of the buffer element
        """
        return self.packet.dest_id



class Link(object):
    """
    Representation of a half-duplex link.

    Note: in the input JSON, the addresses at the ends of the Link will be
    specified, but not the Devices themselves (since those are references).
    """

    def __init__(self, end_1_addr=None, end_2_addr=None, end_1_device=None,
                 end_2_device=None, link_buffer=LinkBuffer(),
                 static_delay_sec=None, capacity_bps=None):
        """
        :ivar string end_1_addr: address of Device on one end (e.g. "H1").
        :ivar string end_2_addr: address of Device on other end.
        :ivar Device end_1_device: actual Device on one end.
        :ivar Device end_2_device: actual Device on the other end.
        :ivar LinkBuffer link_buffer: the link's buffer.
        :ivar float static_delay_sec: link propagation delay in seconds
        :ivar float capacity_bps: max link capacity in bits per second.
        :ivar boolean busy: whether the Link is being used for transmission
        at the moment.
        """
        self.end_1_addr = end_1_addr
        self.end_2_addr = end_2_addr
        self.end_1_device = end_1_device
        self.end_2_device = end_2_device
        self.link_buffer = link_buffer
        self.static_delay_sec = static_delay_sec
        self.capacity_bps = capacity_bps
        self.busy = False

    def __repr__(self):
        return str(self.__dict__)

    def __hash__(self):
        return hash(self.end_1_addr + self.end_2_addr)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.end_1_addr == other.end_1_addr and \
               self.end_2_addr == other.end_2_addr

    def __ne__(self, other):
        return not self.__eq__(other)

    def get_link_cost(self):
        """
        Returns link cost. For now, just returns static propagation delay.
        :return: float of link delay time in seconds
        """

        # TODO consider average wait time for last N packets
        return self.static_delay_sec

    def push(self, packet, global_clock_sec):
        """
        Pushes packet onto own LinkBuffer

        :param Packet packet: Packet to push
        :param global_clock_sec: store when packet pushed
        :return: True if pushed, False if not
        """
        return self.link_buffer.push(packet, global_clock_sec)



class LinkSendEvent(Event):
    """
    Event representing a packet arriving at the Link
    """

    def __init__(self, link):
        """
        :ivar link: link that must send its next packet
        :ivar buff_elem: temporary variable containing LinkBufferElement to send
        """
        self.link = link

    def run(self, main_event_loop, statistics):
        """
        runs by popping off top packet
        :param MainEventLoop main_event_loop: event loop for global timing
        :param Statistics statistics: the Statistics to update
        """

        # sanity check
        if(self.link.queue.empty()):
            logger.warning("LinkSendEvent while Link empty!")
            return

        # now pop
        self.buffer_elem = self.link.pop()

        # update statistics only if not RouterPacket
        if(not isinstance(self.buffer_elem.packet, RouterPacket)):
            statistics.link_packet_transmitted(link, buffer_elem.packet, \
                    main_event_loop.global_cloc_sec)

    def schedule_new_events(self, main_event_loop):
        """
        Schedules new Events. This is called immediately after run().
        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        # schedule a RouterReceivedPacket with propagation + transmission delay
        main_event_loop.schedule_event_with_delay(RouterReceivedPacketEvent(0),\
                self.link.static_delay_sec + self.packet.size_bits / \
                    self.link.capacity_bps)
            # TODO(Laksh): RouterReceivedPacketEvent signature
            # recommended signature RouterReceivedPacketEvent(router, packet)?

        if self.link.link_buffer.queue.empty():
            # if link_buffer.queue is empty, then link is no longer busy
            self.link.busy = False
        else:
            # queue new event with just transmission delay
            main_event_loop.schedule_event_with_delay(LinkSendEvent(self.link),\
                    self.buffer_elem.packet.size_bits / self.link.capacity_bps)



class DeviceToLinkEvent(Event):
    """
    Event representing a packet arriving at the Link
    """

    def __init__(self, packet, link):
        """
        :ivar packet: packet arriving at Link
        :ivar link: link that packet is arriving at
        """
        self.packet = packet
        self.link = link

    def run(self, main_event_loop, statistics):
        """
        runs by trying pushing packet onto link
        :param MainEventLoop main_event_loop: event loop for global timing
        :param Statistics statistics: the Statistics to update
        """
        # if successfully pushed
        if(self.link.push(self.packet, main_event_loop.global_cloc_sec)):
            statistics.link_buffer_occ_change(self, self.packet, \
                    main_event_loop.global_clock_sec) 
        else:
            statistics.link_packet_loss(self.link, main_event_loop.global_clock_sec)

    def schedule_new_events(self, main_event_loop):
        """
        Schedules new Events. This is called immediately after run().
        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        if(not self.link.busy): # only schedule new event if link not busy;
                                # note that dropped packet will be no-op under
                                # this, since link would have to be full and
                                # definitely be busy, which is correct
            main_event_loop.schedule_event_with_delay(LinkSendEvent(self.link), 0) 
            self.link.busy = True
