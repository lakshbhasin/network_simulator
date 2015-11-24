import matplotlib.pyplot as plt
import numpy as np

from common import *

class PlotTool(object):
    """
    Produces graph of different data structures.

    Windowing is used to group together data that occurred between a given
    timestamp and the previous timestamp in the output list (where the
    timestamps are regularly spaced apart in the output list; the constant
    for spacing is defined in common.py).
    """
    @staticmethod
    def gen_count_interval_list(lst):
        """
        Computes a tuple list of counts based on a timestamp list.

        :param list lst: list of timestamps to be converted.
        :return: list: a list of (time, count) tuples where the counts are
        aggregated count of data within the window time.
        """
        # Count within one window interval.
        curr_window_count = 0
        # End point of each window interval.
        curr_window_end_time = GRAPH_WINDOW_SIZE
        output = []
        for idx in range(len(lst)):
            timestamp = lst[idx]
            if timestamp > curr_window_end_time:
                output.append((curr_window_end_time, curr_window_count))
                curr_count = 0
                curr_window_end_time += GRAPH_WINDOW_SIZE
            if timestamp <= curr_window_end_time:
                curr_window_count += 1
        # Append the last elements if they did not reach an end of an
        # interval.
        if curr_window_count != 0:
            output.append((curr_window_end_time, curr_window_count))
        return output

    @staticmethod
    def gen_rate_tuple_list(tuple_list):
        """
        Computes a tuple list of rates based on a (timestamp, packet_size)
        tuple list.

        :param list tuple_list: list of tuples to be converted.
        :return: list: a list of (timestamp, rate in Mbps) where the
        timestamps are multiples of window size and bit rate is
        (packet size) / (time interval).
        """
        curr_bit_sum = 0
        curr_window_end_time = GRAPH_WINDOW_SIZE
        output = []
        for tup_idx in range(len(tuple_list)):
            timestamp, packet_size = tuple_list[tup_idx]
            if timestamp > curr_window_end_time:
                output.append(
                    (curr_window_end_time,
                     float(curr_bit_sum) / GRAPH_WINDOW_SIZE / MEGABIT))
                curr_bit_sum = 0
                curr_window_end_time += GRAPH_WINDOW_SIZE
            if timestamp <= curr_window_end_time:
                curr_bit_sum += packet_size
        # Append the last elements if they did not reach an end of an
        # interval.
        if curr_bit_sum != 0:
            output.append(
                (curr_window_end_time,
                 float(curr_bit_sum) / GRAPH_WINDOW_SIZE / MEGABIT))
        return output

    @staticmethod
    def graph_tuple_list(tuple_list=[], scatter=False):
        """
        Graphs the content of a tuple list.

        :param list tuple_list: current input tuple list to be plotted
        (this list is a 2-D list containing (timestamp, data) tuples).
        :param boolean scatter: if we want a scatter plot, we set this
        variable to True; otherwise, it would be a line graph.
        """
        if not tuple_list:
            return

        if scatter:
            # Scatter plot.
            plt.scatter(*zip(*tuple_list), marker='o', linestyle='--')
        else:
            # Line graph
            plt.plot(*zip(*tuple_list), marker='o', linestyle='--')

    def output_sum_avg_tuple_list(id, value_type, count, units, tuple_list=[]):
        """
        Outputs the average value of a tuple list. This is a simple
        (sum / count) or (sum / time).

        Assume that a tuple list is in the format of (timestamp, data), we
        iterature through the data field of the tuples and outputs the
        average value to std out.

        :param string id: the Device of this average.
        :param string value_type: the data type of the average.
        :param boolean count: whether the denominator of the average is a simple
        count (True), or a timestamp value (False).
        :param string units: units of the average. e.g. "(sec)"
        :param list tuple_list: the tuple list to be computed.
        :return: no return, just print out the statement to stdout.
        """
        curr_sum = 0
        for time, data in tuple_list:
            curr_sum += data
        avg = 0
        if len(tuple_list) != 0:
            if count:
                avg = float(curr_sum) / len(tuple_list)
            else:
                latest_timestamp = tuple_list[len(tuple_list) - 1][0]
                avg = float(curr_sum) / latest_timestamp
        print id + " Average " + value_type + ": " + avg + " " + units

    def output_count_avg_tuple_list(id, value_type, units, tuple_list=[]):
        """
        Outputs the average value of a tuple list. This is (count / time).

        Assume that a tuple list is in the format of (timestamp, data), we
        iterature through the data field of the tuples and outputs the
        average value to std out.

        :param string id: the Device of this average.
        :param string value_type: the data type of the average.
        :param string units: units of the average. e.g. "(sec)"
        :param list tuple_list: the tuple list to be computed.
        :return: no return, just print out the statement to stdout.
        """
        count = len(tuple_list)
        avg = 0
        if count != 0:
            latest_timestamp = tuple_list[len(tuple_list) - 1][0]
            avg = float(count) / latest_timestamp
        print id + " Average " + value_type + ": " + avg + " " + units



class Grapher(object):
    """
    Graphs statistics items from Statistics class.
    """
    def __init__(self, stats=None):
        """
        :ivar Statistics stats: input Statistics object for graphing.
        """
        self.stats = stats

    def graph_links(self):
        """
        Graphs the link stats of each available link.

        This includes buffer occupancy, packet losses, and packet transmitted
        (flow rate).
        """
        # Set up legend storage for link names.
        # Buffer occupancy legend.
        occpy_legend = []
        # Packet loss legend.
        loss_legend = []
        # Packet transmission legend.
        trans_legend = []

        # Iterate through each link to display each stats.
        for link_name, link_stats in self.stats.link_stats.iteritems():
            # Name of link would be "link_name".
            # Buffer occupancy w.r.t time.
            plt.subplot(431)
            PlotTool.graph_tuple_list(link_stats.buffer_occupancy)
            occpy_legend.append(link_name)
            # Output average buffer occupancy to stdout.
            PlotTool.output_sum_avg_tuple_list(
                "Link " + link_name,
                "Buffer Occupancy",
                True, "(pkts)", link_stats.buffer_occupancy)

            # Packet loss times.
            plt.subplot(434)
            loss_count_lst = PlotTool.gen_count_interval_list(
                link_stats.packet_loss_times)
            PlotTool.graph_tuple_list(loss_count_lst)
            loss_legend.append(link_name)
            # Output average packet loss per sec to stdout.
            PlotTool.output_count_avg_tuple_list(
                "Link " + link_name,
                "Packet Loss", "(pkts / sec)",
                link_stats.packet_loss_times)

            # Packet transmission w.r.t time.
            plt.subplot(437)
            flow_rate_list = PlotTool.gen_rate_tuple_list(
                link_stats.packet_transmit_times)
            PlotTool.graph_tuple_list(flow_rate_list)
            trans_legend.append(link_name)
            # Output average packet transmitted per sec to stdout.
            PlotTool.output_count_avg_tuple_list(
                "Link " + link_name,
                "Packet Transmitted", "(pkts / sec)",
                link_stats.packet_transmit_times)

        # Finalize buffer occupancy graph.
        plt.subplot(431)
        plt.legend(occpy_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Buffer Occupancy (pkts)")

        # Finalize loss times graph.
        plt.subplot(434)
        plt.legend(loss_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Packet Losses")

        # Finalize packet transmission graph.
        plt.subplot(437)
        plt.legend(trans_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Flow Rate (Mbps)")

    def graph_flows(self):
        """
        Graphs the flow stats of each available flow.

        This includes flow send and receive rates and packet RTTs.
        """
        # Set up legend storage for flow names.
        # Packet sent rate legend.
        sent_legend = []
        # Packet received rate legend.
        receive_legend = []
        # RTT legend.
        rtt_legend = []
        # Window size legend.
        window_legend = []

        # Iterate through each flow to display each stats.
        for flow_id, flow_stats in self.stats.flow_stats.iteritems():
            # Name of flow would be "flow_id".
            # Packet sent times.
            plt.subplot(432)
            sent_rate_lst = PlotTool.gen_rate_tuple_list(
                flow_stats.packet_sent_times)
            PlotTool.graph_tuple_list(sent_rate_lst)
            sent_legend.append(flow_id)
            # Output average packet sent per sec to stdout.
            PlotTool.output_count_avg_tuple_list(
                "Flow " + flow_id,
                "Packet Sent", "(pkts / sec)",
                flow_stats.packet_sent_times)

            # Packet receive times.
            plt.subplot(435)
            rec_rate_lst = PlotTool.gen_rate_tuple_list(
                flow_stats.packet_rec_times)
            PlotTool.graph_tuple_list(rec_rate_lst)
            receive_legend.append(flow_id)
            # Output average packet received per sec to stdout.
            PlotTool.output_count_avg_tuple_list(
                "Flow " + flow_id,
                "Packet Received", "(pkts / sec)",
                flow_stats.packet_rec_times)

            # Packet RTT times.
            plt.subplot(438)
            PlotTool.graph_tuple_list(flow_stats.packet_rtts)
            rtt_legend.append(flow_id)
            # Output average packet RTT to stdout.
            PlotTool.output_sum_avg_tuple_list(
                "Flow " + flow_id,
                "Packet RTT", True, "(sec)",
                flow_stats.packet_rtts)

            # Window size in packets w.r.t time.
            plt.subplot(4,3,11)
            PlotTool.graph_tuple_list(flow_stats.window_size_times)
            window_legend.append(flow_id)

        # Finalize sent graph.
        plt.subplot(432)
        plt.legend(sent_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Flow send rate (Mbps)")

        # Finalize receive graph.
        plt.subplot(435)
        plt.legend(receive_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Flow Receive Rate (Mbps)")

        # Finalize RTT graph.
        plt.subplot(438)
        plt.legend(rtt_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("RTT (sec)")

        # Finalize window size graph.
        plt.subplot(4,3,11)
        plt.legend(window_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Window Size (pkts)")

    def graph_hosts(self):
        """
        Graphs the host stats of each available host.

        This includes host send and receive rates.
        """
        # Set up legend storage for host names, which are their addresses
        # in strings.
        # Packet sent rate legend.
        sent_legend = []
        # Packet received rate legend.
        receive_legend = []

        # Iterate through each host to display each stats.
        for host_addr, host_stats in self.stats.host_stats.iteritems():
            # Name of host would be "address".
            # Packet sent times.
            plt.subplot(433)
            sent_rate_lst = PlotTool.gen_rate_tuple_list(
                host_stats.packet_sent_times)
            PlotTool.graph_tuple_list(sent_rate_lst)
            sent_legend.append(host_addr)
            # Output average packet received per sec to stdout.
            PlotTool.output_count_avg_tuple_list(
                "Host " + host_addr,
                "Packet Sent", "(pkts / sec)",
                host_stats.packet_sent_times)

            # Packet receive times.
            plt.subplot(436)
            rec_rate_lst = PlotTool.gen_rate_tuple_list(
                host_stats.packet_rec_times)
            PlotTool.graph_tuple_list(rec_rate_lst)
            receive_legend.append(host_addr)
            # Output average packet received per sec to stdout.
            PlotTool.output_count_avg_tuple_list(
                "Host " + host_addr,
                "Packet Received", "(pkts / sec)",
                host_stats.packet_rec_times)

        # Finalize sent graph.
        plt.subplot(433)
        plt.legend(sent_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Host Send Rate (Mbps)")

        # Finalize receive graph.
        plt.subplot(436)
        plt.legend(receive_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Host Receive Rate (Mbps)")

    def graph_network(self):
        """
        Graphs the entire network (this includes all links, flows, and hosts).
        """
        # Set up matplotlib window name.
        fig = plt.figure()
        fig.canvas.set_window_title("Network Statistics")

        # Figure adjust to window size.
        fig.set_size_inches(35, 10.5, forward=True)

        # Graph all three devices.
        self.graph_links()
        self.graph_flows()
        self.graph_hosts()

        # Make spacing between plots.
        plt.tight_layout()
        plt.show()