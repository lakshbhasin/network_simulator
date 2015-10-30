"""
Module for the abstract Flow class, its subclasses (which implement various
TCP algorithms), and Flow-related Events.
"""

from abc import ABCMeta, abstractmethod

from .common import *


class Flow(object):
    """
    Representation of general (abstract) Flow. Subclasses implement specific
    TCP algorithms.
    """
    __metaclass__ = ABCMeta

    def __init__(self, flow_id=None, source_addr=None, dest_addr=None,
                 source=None, dest=None, window_size_packets=None,
                 packets_in_transit=set(), packet_rtts=list(),
                 data_size_bits=None, start_time=None):
        """
        :ivar int flow_id: unique ID for this Flow.
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
        :ivar float start_time: start time relative to global clock.
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
        self.start_time = start_time

    def packet_id_exceeds_data(self, packet_id):
        """
        Checks if a DataPacket's ID is will exceed the amount of data to
        check. If so, this packet ID is too large and should not be sent.
        :param int packet_id: zero-indexed Packet ID
        """
        return (packet_id + 1) * DATA_PACKET_SIZE_BITS > self.data_size_bits

    def get_window_size(self):
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

# TODO(team): Flow-related Event subclasses
# TODO(team): Flow subclasses for at least two TCP algorithms.
