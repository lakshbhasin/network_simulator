"""
Module for the Statistics class, and other statistics-related details (e.g.
graphing).
"""

from packet import *


class LinkStats(object):
    """
    Contains information of a link related to per-link buffer occupancy,
    packet loss, and flow rate.

    :ivar list buffer_occupancy: a list of (timestamp, buffer_occupancy)
    tuples.
    :ivar list packet_loss_times: a list of timestamps, each corresponds
    to a packet loss.
    :ivar list packet_transmit_times: a list of (timestamp, packet_size)
    corresponding to when a packet was transmitted. packet_size is in bits.
    """
    def __init__(self):
        self.buffer_occupancy = []
        self.packet_loss_times = []
        self.packet_transmit_times = []


class FlowStats(object):
    """
    Contains information of a flow related to timestamps of each sending
    and receiving.

    :ivar list packet_sent_times: a list of (timestamp, packet_size)
    tuples. packet_size is in bits. Time is in seconds.
    :ivar list packet_rec_times: a list of (timestamp, packet_size)
    tuples. packet_size is in bits. Time is in seconds.
    :ivar list packet_rtts: a list of RTTs (timestamp, RTT) tuples where
    RTTs are given in seconds.
    :ivar list window_size_times: a list of (timestamp, window_size) with
    timestamps in seconds and window_size in number of packets.
    """
    def __init__(self):
        self.packet_sent_times = []
        self.packet_rec_times = []
        self.packet_rtts = []
        self.window_size_times = []


class HostStats(object):
    """
     Contains information of a host related to per-host send/receive rate.

    :ivar list packet_sent_times: a list of (timestamp, packet_size)
    tuples. packet_size is in bits. Time is in seconds.
    :ivar list packet_rec_times: a list of (timestamp, packet_size)
    tuples. packet_size is in bits. Time is in seconds.
    """
    def __init__(self):
        self.packet_sent_times = []
        self.packet_rec_times = []


class Statistics(object):
    """
    Intended to be owned by the main loop to record all statistics within
    the network.

    :ivar dict link_stats: a map from link name to :class:`.LinkStats`.
    :ivar dict flow_stats: a map from flow ID to :class:`.FlowStats`. flow
    ids are strings.
    :ivar dict host_stats: a map from host ID to :class:`.HostStats`. host
    ids are strings.
    """
    def __init__(self):
        self.link_stats = dict()
        self.flow_stats = dict()
        self.host_stats = dict()

    def get_link_stats(self, link):
        """
        Check whether a link has already existed in the dictionary; if so,
        skip the rest of the steps and return the stats object. If not,
        create a new mapping then return the stats object.

        :param Link link: link to be determined.
        :return :class:`.LinkStats`.
        """
        if link.name not in self.link_stats:
            self.link_stats[link.name] = LinkStats()
        return self.link_stats[link.name]

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
        buffer_occ_packets = link.link_buffer.get_num_packets()
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
        # Make sure the packet received is a data packet.
        assert isinstance(data_packet, DataPacket)

        stats = self.get_flow_stats(flow)
        stats.packet_sent_times.append(
            (data_packet.start_time_sec, data_packet.size_bits))

    def flow_packet_received(self, flow, ack_packet, curr_time):
        """
        Record an ack packet received by a flow.

        :param Flow flow: flow of action.
        :param AckPacket ack_packet: ack packet received.
        :param float curr_time: simulation time of reception.
        """
        # Make sure the packet received is an ACK packet.
        assert isinstance(ack_packet, AckPacket)

        stats = self.get_flow_stats(flow)
        stats.packet_rec_times.append((curr_time, ack_packet.size_bits))
        # Retrieve data packet sent time from the ack packet and use
        # it to calculate RTT.
        sent_time = ack_packet.data_packet_start_time_sec
        stats.packet_rtts.append((curr_time, curr_time - sent_time))

    def flow_window_size_update(self, flow, curr_time):
        """
        Record a change in window size from a flow.

        :param Flow flow: flow of action.
        :param float curr_time: simulation time of change.
        """
        # TODO(laksh): Incorporate this into flow.py code to plot.
        stats = self.get_flow_stats(flow)
        stats.window_size_times.append((curr_time, flow.window_size_packets))

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
