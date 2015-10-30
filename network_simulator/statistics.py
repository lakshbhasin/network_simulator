"""
Module for the Statistics class, and other statistics-related details (e.g.
graphing).
"""


from .host import *
from .link import *
from .flow import *


class LinkStats(object):
    """
    Contains information of a link regarding to per-link buffer occupancy,
    packet loss, and flow rate.

    :ivar list buffer_occupancy: a list of (timestamp, buffer_occupancy)
    tuples.
    :ivar list packet_loss_times: a list of timestamps, each corresponding
    to a packet loss.
    :ivar list packet_transmit_times: a list of timestamps corresponding
    to when a packet was transmitted.
    """
    def __init__(self, buffer_occupancy=0, packet_loss_times=[],
                 packet_transmit_times=[]):
        self.buffer_occupancy = buffer_occupancy
        self.packet_loss_times = packet_loss_times
        self.packet_transmit_times = packet_transmit_times

    # TODO(sharon): functions and subclasses/events (if any) goes here.


class FlowStats(object):
    """
    Contains information of a flow regarding to per-flow send/receive rate
    and packet round-trip delay.

    :ivar list packet_sent_times_sec: a list of timestamps corresponding to
    when a data packet was sent.
    :ivar list packet_rec_times_sec: a list of timestamps corresponding to
    when an ACK packet was received for a given :class:`.Flow`.
    :ivar list packet_rtts_sec: a list of RTTs (in seconds).
    """
    def __init__(self, packet_sent_times_sec=[], packet_rec_times_sec=[],
                 packet_rtts_sec=[]):
        packet_sent_times_sec = packet_sent_times_sec
        packet_rec_times_sec = packet_rec_times_sec
        packet_rtts_sec = packet_rtts_sec

    # TODO(sharon): functions and subclasses/events (if any) goes here.


class HostStats(object):
    """
     Contains information of a host regarding to per-host send/receive rate.

    :ivar list packet_sent_times_sec: a list of (timestamp, packet_size)
    tuples.
    :ivar list packet_rec_times_sec: a list of (timestamp, packet_size)
    tuples.
    """
    def __init__(self, packet_sent_times_sec=[], packet_rec_times_sec=[]):
        packet_sent_times_sec = packet_sent_times_sec
        packet_rec_times_sec = packet_rec_times_sec

    # TODO(sharon): functions and subclasses/events (if any) goes here.


class Statistics(object):
    """
    Intended to be owned by the main loop to record all statistics within
    the network.

    :ivar dict link_stats: a map from (end_1_id, end_2_id) to
    :class:`.LinkStats`.
    :ivar dict flow_stats: a map from flow ID to :class:`.FlowStats`.
    :ivar dict host_stats: a map from host ID to :class:`.HostStats`.
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
        """
        # Create a tuple of the pair and check if it exists in the dict.
        tup = (link.end_1_addr, link.end_2_addr)

        if tup not in self.link_stats:
            self.link_stats[tup] = LinkStats
        return self.link_stats[tup]

    def get_flow_stats(self, flow):
        """
        Check whether a flow has already existed in the dictionary; if so,
        skip the rest of the steps and return the stats object. If not,
        create a new mapping then return the stats object.

        :param Flow flow: flow to be determined.
        """
        if flow.id not in self.flow_stats:
            self.flow_stats[flow.id] = FlowStats
        return self.flow_stats[flow.id]

    def get_host_stats(self, host):
        """
        Check whether a host has already existed in the dictionary; if so,
        skip the rest of the steps and return the stats object. If not,
        create a new mapping then return the stats object.

        :param Host host: host to be determined.
        """
        if host.address not in self.host_stats:
            self.host_stats[host.address] = HostStats
        return self.host_stats[host.address]

    def link_packet_loss(self, link, curr_time):
        """
        Record a packet loss of a link.

        :param link: link of action.
        :param curr_time: simulation time of loss.
        """
        stats = self.get_link_stats(link)
        # TODO(team): Is this the most efficient?
        stats.buffer_occupancy.append((curr_time, link.buffer_occupancy))
        stats.packet_loss_times.append(curr_time)

    def link_packet_transmitted(self, link, curr_time):
        """
        Record a packet transmission of a link.

        :param link: link of action.
        :param curr_time: simulation time of transmission.
        """
        stats = self.get_link_stats(link)
        stats.buffer_occupancy.append((curr_time, link.buffer_occupancy))
        stats.packet_transmit_times.append(curr_time)

    def flow_packet_sent(self, flow, curr_time):
        """
        Record a packet sent from a flow.

        :param flow: flow of action.
        :param curr_time: simulation time of sending.
        """
        stats = self.get_flow_stats(flow)
        stats.packet_sent_times_sec.append(curr_time)

    def flow_packet_received(self, flow, curr_time):
        """
        Record a packet received by a flow.

        :param flow: flow of action.
        :param curr_time: simulation time of reception.
        """
        stats = self.get_flow_stats(flow)
        stats.packet_rec_times_sec.append(curr_time)
        # Retrieve the last element on the sent_times list to find
        # the corresponding sent time and using the diff we can
        # determine the rtt time.
        sent_time = stats.packet_sent_times_sec[-1]
        stats.packet_rtts_sec.append(curr_time - sent_time)

    def host_packet_sent(self, host, curr_time):
        """
        Record a packet sent from a host.

        :param host: host of action.
        :param curr_time: simulation time of sending.
        """
        stats = self.get_host_stats(host)
        stats.packet_sent_times_sec.append(curr_time)

    def host_packet_received(self, host, curr_time):
        """
        Record a packet received by a host.

        :param host: host of action.
        :param curr_time: simulation time of reception.
        """
        stats = self.get_host_stats(host)
        stats.packet_rec_times_sec.append(curr_time)