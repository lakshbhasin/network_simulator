"""
Module for the Statistics class, and other statistics-related details (e.g.
graphing).
"""


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
    def __init__(self, buffer_occupancy=[], packet_loss_times=[],
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

    # TODO(sharon): functions and subclasses/events (if any) goes here.
