"""
Module for the Statistics class, and other statistics-related details (e.g.
graphing).
"""


from host import *
from link import *
from flow import *


class LinkStats(object):
    """
    Contains information of a link related to per-link buffer occupancy,
    packet loss, and flow rate.

    :ivar list buffer_occupancy: a list of (timestamp, buffer_occupancy)
    tuples.
    :ivar list packet_loss_times: a list of timestamps, each corresponding
    to a packet loss.
    :ivar list packet_transmit_times: a list of (timestamp, packet_size)
    corresponding to when a packet was transmitted. packet_size is in bits.
    """
    def __init__(self, buffer_occupancy=[], packet_loss_times=[],
                 packet_transmit_times=[]):
        self.buffer_occupancy = buffer_occupancy
        self.packet_loss_times = packet_loss_times
        self.packet_transmit_times = packet_transmit_times



class FlowStats(object):
    """
    Contains information of a flow related to timestamps of each sending
    and receiving.

    :ivar list packet_sent_times: a list of timestamps corresponding to
    when a data packet was sent. Time is in seconds.
    :ivar list packet_rec_times: a list of timestamps corresponding to
    when an ACK packet was received for this :class:`.Flow`. Time is in
    seconds.
    :ivar list packet_rtts: a list of RTTs (in seconds).
    """
    def __init__(self, packet_sent_times=[], packet_rec_times=[],
                 packet_rtts=[]):
        packet_sent_times = packet_sent_times
        packet_rec_times = packet_rec_times
        packet_rtts = packet_rtts



class HostStats(object):
    """
     Contains information of a host related to per-host send/receive rate.

    :ivar list packet_sent_times: a list of (timestamp, packet_size)
    tuples. packet_size is in bits. Time is in seconds.
    :ivar list packet_rec_times: a list of (timestamp, packet_size)
    tuples. packet_size is in bits. Time is in seconds.
    """
    def __init__(self, packet_sent_times=[], packet_rec_times=[]):
        packet_sent_times = packet_sent_times
        packet_rec_times = packet_rec_times



class Statistics(object):
    """
    Intended to be owned by the main loop to record all statistics within
    the network.

    :ivar dict link_stats: a map from (end_1_id, end_2_id) to
    :class:`.LinkStats`. end_id's are strings.
    :ivar dict flow_stats: a map from flow ID to :class:`.FlowStats`. flow
    ids are strings.
    :ivar dict host_stats: a map from host ID to :class:`.HostStats`. host
    ids are strings.
    """
    def __init__(self, link_stats={}, flow_stats={}, host_stats={}):
        self.link_stats = link_stats
        self.flow_stats = flow_stats
        self.host_stats = host_stats

    def get_link_stats(self, link):
        """
        Check whether a link has already existed in the dictionary; if so,
        skip the rest of the steps and return the stats object. If not,
        create a new mapping then return the stats object.

        :param Link link: link to be determined.
        :return :class:`.LinkStats`.
        """
        # Create a tuple of the pair and check if it exists in the dict.
        tup = (link.end_1_addr, link.end_2_addr)

        if tup not in self.link_stats:
            self.link_stats[tup] = LinkStats()
        return self.link_stats[tup]

    def get_flow_stats(self, flow):
        """
        Check whether a flow has already existed in the dictionary; if so,
        skip the rest of the steps and return the stats object. If not,
        create a new mapping then return the stats object.

        :param Flow flow: flow to be determined.
        :return :class:`.FlowStats`.
        """
        if flow.flow_id not in self.flow_stats:
            self.flow_stats[flow.flow_id] = FlowStats()
        return self.flow_stats[flow.flow_id]

    def get_host_stats(self, host):
        """
        Check whether a host has already existed in the dictionary; if so,
        skip the rest of the steps and return the stats object. If not,
        create a new mapping then return the stats object.

        :param Host host: host to be determined.
        :return :class:`.HostStats`.
        """
        if host.address not in self.host_stats:
            self.host_stats[host.address] = HostStats()
        return self.host_stats[host.address]

    def link_buffer_occ_change(self, link, curr_time):
        """
        Update the buffer size as a link gains or loses a queue element.

        :param Link link: link that has a change of buffer size.
        :param float curr_time: time of occupancy change.
        """
        stats = self.get_link_stats(link)
        # TODO(sharon): Check with Cody if qsize() is what is want here (count
        # number of all packets). Or do we just want to size of
        # RoutingPackets.
        buffer_occ_packets = link.link_buffer.qsize()
        stats.buffer_occupancy.append((curr_time, buffer_occ_packets))

    def link_packet_loss(self, link, curr_time):
        """
        Record a packet loss of a link.

        :param Link link: link of action.
        :param float curr_time: simulation time of loss.
        """
        stats = self.get_link_stats(link)
        stats.packet_loss_times.append(curr_time)

    def link_packet_transmitted(self, link, packet, curr_time):
        """
        Record a packet transmission of a link.

        :param Link link: link of action.
        :param Packet packet: the packet transmitting.
        :param float curr_time: simulation time of transmission.
        """
        stats = self.get_link_stats(link)
        stats.packet_transmit_times.append((curr_time, packet.size_bits))

    def flow_packet_sent(self, flow, data_packet):
        """
        Record a data packet sent from a flow.

        :param Flow flow: flow of action.
        :param DataPacket data_packet: data packet to send.
        """
        stats = self.get_flow_stats(flow)
        stats.packet_sent_times.append(data_packet.start_time_sec)

    def flow_packet_received(self, flow, ack_packet, curr_time):
        """
        Record an ack packet received by a flow.

        :param Flow flow: flow of action.
        :param AckPacket ack_packet: ack packet received.
        :param float curr_time: simulation time of reception.
        """
        stats = self.get_flow_stats(flow)
        stats.packet_rec_times.append(curr_time)
        # Retrieve data packet sent time from the ack packet and use
        # it to calculate RTT.
        sent_time = ack_packet.data_packet_start_time_sec
        stats.packet_rtts.append(curr_time - sent_time)

    def host_packet_sent(self, host, packet):
        """
        Record a packet sent from a host.

        :param Host host: host of action.
        :param Packet packet: packet sent out.
        """
        stats = self.get_host_stats(host)
        stats.packet_sent_times.append((packet.start_time_sec,
                                        packet.size_bits))

    def host_packet_received(self, host, packet, curr_time):
        """
        Record a packet received by a host.

        :param Host host: host of action.
        :param Packet packet: packet received.
        :param float curr_time: time of receive.
        """
        stats = self.get_host_stats(host)
        stats.packet_rec_times.append((curr_time, packet.size_bits))