"""
This module will hold the class Packet, subclasses of Packet,
and various Packet-related Events.
Packet will be an abstract class.
"""

from abc import ABCMeta
from common import *


class Packet(object):
    """
    Packets are units of information in the network.
    They are generated by a flow; all packets in the same flow have the same
     destination network address.
    Packets can be router packets, data packets, or ACKs.
    All of these have a fixed size specified in common.py.

    :ivar int id: an id field, used by the Flow to
        keep track of the packets and their ACKs,
        and to know when to retransmit. These are zero-indexed.
    :ivar int flow_ID: the flow to which this packet belongs.
        So, (flow_ID, packet_ID) uniquely identifies a given data packet.
    :ivar string source_ID: source Device ID.
    :ivar string dest_ID: destination Device ID.
    :ivar float start_time_sec: time at which the packet
        was created (in sec).
    :ivar int size_bits: size of the packet in bits.
    """
    __metaclass__ = ABCMeta

    def __init__(self, packet_id=None, flow_id=None, source_id=None,
                 dest_id=None,
                 start_time_sec=None, size_bits=None):

        self.packet_id = packet_id
        self.flow_id = flow_id
        self.source_id = source_id
        self.dest_id = dest_id
        self.start_time_sec = start_time_sec
        self.size_bits = size_bits

    def __eq__(self, other):
        return other.__class__ == self.__class__ and \
            self.packet_id == other.packet_id


class DataPacket(Packet):
    """
    DataPacket class: a packet used for transferring data between Hosts.
    """

    def __init__(self, packet_id=None, flow_id=None, source_id=None,
                 dest_id=None, start_time_sec=None):
        Packet.__init__(self, packet_id=packet_id, flow_id=flow_id,
                        source_id=source_id, dest_id=dest_id,
                        start_time_sec=start_time_sec,
                        size_bits=DATA_PACKET_SIZE_BITS)


class AckPacket(Packet):
    """
    AckPacket class: a packet used for sending ACKs between Hosts.

    :ivar list flow_packets_received: an ascending,
    sorted list of all of the packet IDs
    that have been received by the destination Host.
    This is used to implement selective repeat.
    :ivar float data_packet_start_time_sec: start time of data packet sending.
    :ivar bool loss_occurred: whether this ACK's flow_packets_received
    contains gaps that indicate a loss occurred. This is currently set in
    FlowReceivedAckEvent.
    """

    def __init__(self, packet_id=None, flow_id=None, source_id=None,
                 dest_id=None, start_time_sec=None, flow_packets_received=[],
                 data_packet_start_time_sec=None):
        Packet.__init__(self, packet_id=packet_id, flow_id=flow_id,
                        source_id=source_id, dest_id=dest_id,
                        start_time_sec=start_time_sec,
                        size_bits=ACK_PACKET_SIZE_BITS)

        self.flow_packets_received = flow_packets_received
        self.data_packet_start_time_sec = data_packet_start_time_sec
        self.loss_occurred = False  # is set in flow.py


class RouterPacket(Packet):
    """
    RouterPacket class: a packet used to update routing tables between Routers.
    The information sent is the known *min* cost to travel from "this" Router
    (i.e. the one generating the packet) and a given Host.

    :ivar map router_to_host_dists: a map from RouterHost to *min* distance (in
        sec) between the Router and Host. The RouterHost represents the
        Router generating this packet and the Host represents one of its
        known Hosts. Costs are *min* costs.
    """
    def __init__(self, source_id=None, dest_id=None, start_time_sec=None,
                 router_to_host_dists=dict()):
        Packet.__init__(self, packet_id=ROUTER_PACKET_DEFAULT_ID,
                        flow_id=None,
                        source_id=source_id, dest_id=dest_id,
                        start_time_sec=start_time_sec,
                        size_bits=ROUTER_PACKET_SIZE_BITS)
        self.router_to_host_dists = router_to_host_dists

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.router_to_host_dists == other.router_to_host_dists
