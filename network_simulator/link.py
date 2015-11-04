"""
This module holds the Link class, the LinkBuffer class, the LinkBufferElement
class, and various Link-related Events.
"""

from Queue import Queue
from packet import *
from common import *
from event import *

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
        """
        self.max_buffer_size_bits = max_buffer_size_bits
        self.queue = queue
        self.curr_buffer_size_bits = 0 # size of current buffer in bits

    def __repr__(self):
        return str(self.__dict__)

    def remaining(self):
        """
        returns remaining size in buffer in bits
        :return: remaining buffer size in bits
        """
        return self.max_buffer_size_bits - self.curr_buffer_size_bits

    def push(self, packet, dest_device_addr):
        """
        :param Packet packet: Packet to push
        :param string dest_device_addr: destination device of packet

        Pushes packet onto LinkBuffer going towards dest_device_addr
        :return: True if pushed, False if not
        """
        if isinstance(packet, RouterPacket):
            # always push RouterPacket
            self.queue.put(LinkBufferElement(packet, dest_device_addr))
            self.curr_buffer_size_bits += ROUTER_PACKET_SIZE_BITS
            return True

        elif self.remaining() > DATA_PACKET_SIZE_BITS and \
                isinstance(packet, DataPacket):
            # if DataPacket & has room
            self.curr_buffer_size_bits += DATA_PACKET_SIZE_BITS
            self.queue.put(LinkBufferElement(packet, dest_device_addr))

        elif self.remaining() > ACK_PACKET_SIZE_BITS and \
                isinstance(packet, AckPacket):
            # if AckPacket & has room
            self.curr_buffer_size_bits += ACK_PACKET_SIZE_BITS
            self.queue.put(LinkBufferElement(packet, dest_device_addr))

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
    # TODO(yubo) timestamp entering buffer (pull from DeviceToLinkEvent)

    def __init__(self, packet, dest_device_addr):
        """
        :ivar Packet packet
        :ivar string dest_device_addr
        """
        self.packet = packet
        self.dest_device_addr = dest_device_addr

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

class LinkSendEvent(Event):
    """
    Event representing a packet arriving at the Link
    """

    def __init__(self, link):
        """
        :ivar link: link that must send its next packet
        """
        self.link = link
        self.buffer_elem = None
    def run(self, statistics):
        """
        runs by popping off top packet
        :param Statistics statistics: the Statistics to update
        """
        self.buffer_elem = self.link.pop()
        statistics.link_packet_transmitted(link, buffer_elem.packet, 0) # TODO get global time

    def schedule_new_events(self, main_event_loop):
        """
        Schedules new Events. This is called immediately after run().
        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        main_event_loop.schedule_event_with_delay(new RouterReceivedPacketEvent(0)) # TODO get RouterReceivedPacketEvent
                                                                                    # specs
        # if link_buffer.queue is empty, then link is no longer busy
        if self.link.link_buffer.queue.empty():
            self.link.busy = False
class DeviceToLinkEvent(Event):
    """
    Event representing a packet arriving at the Link
    """

    def __init__(self, packet, link, dest_device_addr):
        """
        :ivar packet: packet arriving at Link
        :ivar link: link that packet is arriving at
        :ivar dest_device_addr: destination of packet
        """
        self.packet = packet
        self.link = link
        self.dest_device_addr = dest_device_addr

    def run(self, statistics):
        """
        runs by trying pushing packet onto link
        :param Statistics statistics: the Statistics to update
        """
        # if successfully pushed
        if(self.link.push(self.packet, self.dest_device_addr)):
            statistics.link_buffer_occ_change(self, self.packet, 0) # TODO update to global time
        else:
            statistics.link_packet_loss(self, 0) # TODO global time

    def schedule_new_events(self, main_event_loop):
        """
        Schedules new Events. This is called immediately after run().
        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        if(not self.link.busy): # only schedule new event if link not busy; note that dropped packet
                                # is a sub-category of this, since link would have to be full and definitely be busy
            main_event_loop.schedule_event_with_delay(new LinkSendEvent(self.link),0) # TODO linkSendEvent
            self.link.busy = True
