"""
This module holds the Link class, the LinkBuffer class, the LinkBufferElement
class, and various Link-related Events.
"""

from Queue import Queue

# TODO(yubo): Finish implementing the classes and Events for this.


class Link(object):
    """
    Representation of a half-duplex link.

    Note: in the input JSON, the addresses at the ends of the Link will be
    specified, but not the Devices themselves (since those are references).
    """

    def __init__(self, end_1_addr=None, end_2_addr=None, end_1_device=None,
                 end_2_device=None, buffer=None, static_delay_sec=None,
                 capacity_bps=None):
        """
        :ivar string end_1_addr: address of Device on one end (e.g. "H1").
        :ivar string end_2_addr: address of Device on other end.
        :ivar Device end_1_device: actual Device on one end.
        :ivar Device end_2_device: actual Device on the other end.
        :ivar LinkBuffer buffer: the link's buffer.
        :ivar float static_delay_sec: link propagation delay.
        :ivar float capacity_bps: max link capacity in bits per second.
        :ivar boolean busy: whether the Link is being used for transmission
        at the moment.
        """
        self.end_1_addr = end_1_addr
        self.end_2_addr = end_2_addr
        self.end_1_device = end_1_device
        self.end_2_device = end_2_device
        self.buffer = buffer
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


class LinkBuffer(object):
    """
    Representation of a Link's FIFO buffer.

    TODO(team): Parameters related to link congestion, so we can have dynamic
    routing table updates.
    TODO(yubo): Functions for whether this is full etc.
    """

    def __init__(self, buffer_size_bits=None, queue=None):
        """
        :ivar int buffer_size_bits: maximum buffer size in bits.
        :ivar Queue queue: a FIFO queue of LinkBufferElements
        """
        self.buffer_size_bits = buffer_size_bits
        self.queue = queue

    def __repr__(self):
        return str(self.__dict__)


class LinkBufferElement(object):
    """
    Wrapper class containing a Packet and which Device address it's going to
    (i.e. the direction).
    """

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
