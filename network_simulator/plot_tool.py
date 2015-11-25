import matplotlib.pyplot as plt
import numpy as np

from common import *
import logging

logger = logging.getLogger(__name__)


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
                curr_window_count = 0
                curr_window_end_time += GRAPH_WINDOW_SIZE
            if timestamp <= curr_window_end_time:
                curr_window_count += 1
        # Append the last elements if they did not reach an end of an
        # interval.
        if curr_window_count != 0:
            output.append((curr_window_end_time, curr_window_count))
        return output

    @staticmethod
    def gen_windowed_buffer_occ_list(buffer_occupancy,
                                     window_size=BUFFER_OCC_WINDOW_SIZE):
        """
        A helper function for plotting buffer occupancies with windows. This
        function works by looking at buffer occupancy updates within a given
        window size, and it takes the **maximum** buffer occupancy as the
        representative occupancy for that window. If no updates were recorded
        in that window, the previous window's buffer occupancy value is used.

        :param buffer_occupancy: a list of (timestamp, buffer_occ) tuples
        that only records **changes** in the buffer occupancy.
        :param window_size: The window size used for computing occupancies.
        :return: a list of (window_end_time, max_buffer_occ) tuples.
        """
        # The current maximum buffer occupancy in this window
        max_buffer_occ_in_wind = 0.0
        # The previous window's maximum buffer occupancy
        prev_wind_max_buffer_occ = 0.0
        # The end time of the sliding window used.
        curr_window_end_time = window_size

        windowed_buffer_occ = []
        for tup_idx in range(len(buffer_occupancy)):
            timestamp, this_buffer_occ = buffer_occupancy[tup_idx]
            if timestamp > curr_window_end_time:
                # If there were no buffer occupancy updates in this
                # window, use the previous window's value (i.e. occupancy
                # is unchanged).
                if max_buffer_occ_in_wind == 0.0:
                    max_buffer_occ_in_wind = prev_wind_max_buffer_occ

                windowed_buffer_occ.append((curr_window_end_time,
                                            max_buffer_occ_in_wind))

                # Advance by a window.
                prev_wind_max_buffer_occ = max_buffer_occ_in_wind
                max_buffer_occ_in_wind = 0.0
                curr_window_end_time += window_size
            if timestamp <= curr_window_end_time:
                max_buffer_occ_in_wind = max(max_buffer_occ_in_wind,
                                             this_buffer_occ)
        # Append the last elements if they did not reach an end of an
        # interval.
        if max_buffer_occ_in_wind != 0.0:
            windowed_buffer_occ.append(
                (curr_window_end_time, max_buffer_occ_in_wind))

        return windowed_buffer_occ

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
    def graph_tuple_list(tuple_list, scatter=False):
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
            plt.scatter(*zip(*tuple_list), linestyle='--')
        else:
            # Line graph
            plt.plot(*zip(*tuple_list), linestyle='--')

    @staticmethod
    def output_sum_avg_tuple_list(id, value_type, count, units, tuple_list):
        """
        Outputs the average value of a tuple list. This is a simple
        (sum / count) or (sum / time).

        Assume that a tuple list is in the format of (timestamp, data), we
        iterate through the data field of the tuples and log the average
        value.

        :param string id: the Device of this average.
        :param string value_type: the data type of the average.
        :param boolean count: whether the denominator of the average is a simple
        count (True), or a timestamp value (False).
        :param string units: units of the average. e.g. "(sec)"
        :param list tuple_list: the tuple list to be computed.
        :return: no return, just log average value.
        """
        curr_sum = 0
        for time, data in tuple_list:
            curr_sum += data
        avg = 0
        if len(tuple_list) != 0:
            if count:
                avg = float(curr_sum) / len(tuple_list)
            else:
                latest_timestamp = tuple_list[-1][0]
                avg = float(curr_sum) / latest_timestamp
        logger.info("%s Average %s: %f %s", id, value_type, avg, units)

    @staticmethod
    def output_rate_avg_tuple_list(id, value_type, units, tuple_list):
        """
        Outputs the average rate of a tuple list. This is (total Mb / time).

        Assume that the list contains (timestamp, packet_size in bits) tuples,
        we calculate the rate over time and log the result.

        :param string id: the Device of this average.
        :param string value_type: the data type of the average.
        :param string units: units of the average. e.g. "(sec)"
        :param list tuple_list: the list to be computed.
        :return: no return, just log average value.
        """
        curr_sum = 0
        for time, data in tuple_list:
            curr_sum += data
        avg = 0
        if len(tuple_list) != 0:
            latest_timestamp = tuple_list[-1][0]
            # Convert from bit / sec Mbps
            avg = float(curr_sum) / latest_timestamp / MEGABIT
        logger.info("%s Average %s: %f %s", id, value_type, avg, units)

    @staticmethod
    def output_count_avg_list(id, value_type, units, lst):
        """
        Outputs the average count value of a list. This is (count / time)
        where count = len(tuple_list).

        Assume that the list contains timestamps, we calculate the count
        over time and log the result.

        :param string id: the Device of this average.
        :param string value_type: the data type of the average.
        :param string units: units of the average. e.g. "(sec)"
        :param list lst: the list to be computed.
        :return: no return, just log average value.
        """
        count = len(lst)
        avg = 0
        if count != 0:
            latest_timestamp = lst[-1]
            avg = float(count) / latest_timestamp
        logger.info("%s Average %s: %f %s", id, value_type, avg, units)


class Analyzer(object):
    """
    Graphs statistics items from Statistics class and logs averages of data
    for each network device.
    """
    def __init__(self, stats):
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
        for link_name, link_stats in sorted(self.stats.link_stats.iteritems()):
            # Name of link would be "link_name".
            # Buffer occupancy w.r.t time.
            plt.subplot(4, 3, 1)

            # buffer_occupancy only records changes, so we need to window it
            # appropriately before graphing.
            windowed_buffer_occ = PlotTool.gen_windowed_buffer_occ_list(
                link_stats.buffer_occupancy)
            PlotTool.graph_tuple_list(windowed_buffer_occ)
            occpy_legend.append(link_name)
            # Output average buffer occupancy to log.
            PlotTool.output_sum_avg_tuple_list(
                id="Link " + link_name,
                value_type="Buffer Occupancy",
                count=True, units="(pkts)",
                tuple_list=link_stats.buffer_occupancy)

            # Packet loss times.
            plt.subplot(4, 3, 4)
            loss_count_lst = PlotTool.gen_count_interval_list(
                link_stats.packet_loss_times)
            PlotTool.graph_tuple_list(loss_count_lst)
            loss_legend.append(link_name)
            # Output average packet loss per sec to log.
            PlotTool.output_count_avg_list(
                id="Link " + link_name,
                value_type="Packet Loss", units="(pkts / sec)",
                lst=link_stats.packet_loss_times)

            # Packet transmission w.r.t time.
            plt.subplot(4, 3, 7)
            flow_rate_list = PlotTool.gen_rate_tuple_list(
                link_stats.packet_transmit_times)
            PlotTool.graph_tuple_list(flow_rate_list)
            trans_legend.append(link_name)
            # Output average packet transmitted per sec to log.
            PlotTool.output_rate_avg_tuple_list(
                id="Link " + link_name,
                value_type="Transmission Rate", units="(Mbps)",
                tuple_list=link_stats.packet_transmit_times)

        # Finalize buffer occupancy graph.
        plt.subplot(4, 3, 1)
        plt.legend(occpy_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Buffer Occupancy (pkts)")

        # Finalize loss times graph.
        plt.subplot(4, 3, 4)
        plt.legend(loss_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Packet Losses")

        # Finalize packet transmission graph.
        plt.subplot(4, 3, 7)
        plt.legend(trans_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Transmission Rate (Mbps)")

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
        for flow_id, flow_stats in sorted(self.stats.flow_stats.iteritems()):
            # Packet receive times.
            plt.subplot(4, 3, 2)
            rec_rate_lst = PlotTool.gen_rate_tuple_list(
                flow_stats.packet_rec_times)
            PlotTool.graph_tuple_list(rec_rate_lst)
            receive_legend.append(flow_id)
            # Output average packet received per sec to log.
            PlotTool.output_rate_avg_tuple_list(
                id="Flow " + flow_id,
                value_type="Receive Rate", units="(Mbps)",
                tuple_list=flow_stats.packet_rec_times)

            # Name of flow would be "flow_id".
            # Packet sent times.
            plt.subplot(4, 3, 5)
            sent_rate_lst = PlotTool.gen_rate_tuple_list(
                flow_stats.packet_sent_times)
            PlotTool.graph_tuple_list(sent_rate_lst)
            sent_legend.append(flow_id)
            # Output average packet sent per sec to log.
            PlotTool.output_rate_avg_tuple_list(
                id="Flow " + flow_id,
                value_type="Send Rate", units="(Mbps)",
                tuple_list=flow_stats.packet_sent_times)

            # Window size in packets w.r.t time.
            plt.subplot(4, 3, 8)
            PlotTool.graph_tuple_list(flow_stats.window_size_times)
            window_legend.append(flow_id)
            # Output average window size to log.
            PlotTool.output_sum_avg_tuple_list(
                id="Flow " + flow_id,
                value_type="Window Size", count=True, units="(pkts)",
                tuple_list=flow_stats.window_size_times)

            # Packet RTT times.
            plt.subplot(4, 3, 11)
            PlotTool.graph_tuple_list(flow_stats.packet_rtts)
            rtt_legend.append(flow_id)
            # Output average packet RTT to log.
            PlotTool.output_sum_avg_tuple_list(
                id="Flow " + flow_id,
                value_type="Packet RTT", count=True, units="(sec)",
                tuple_list=flow_stats.packet_rtts)

        # Finalize receive graph.
        plt.subplot(4, 3, 2)
        plt.legend(receive_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Flow Receive Rate (Mbps)")

        # Finalize sent graph.
        plt.subplot(4, 3, 5)
        plt.legend(sent_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Flow send rate (Mbps)")

        # Finalize window size graph.
        plt.subplot(4, 3, 8)
        plt.legend(window_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Window Size (pkts)")

        # Finalize RTT graph.
        plt.subplot(4, 3, 11)
        plt.legend(rtt_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("RTT (sec)")

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
        for host_addr, host_stats in sorted(self.stats.host_stats.iteritems()):
            # Name of host would be "address".
            # Packet sent times.
            plt.subplot(4, 3, 3)
            sent_rate_lst = PlotTool.gen_rate_tuple_list(
                host_stats.packet_sent_times)
            PlotTool.graph_tuple_list(sent_rate_lst)
            sent_legend.append(host_addr)
            # Output average packet received per sec to log.
            PlotTool.output_rate_avg_tuple_list(
                id="Host " + host_addr,
                value_type="Send Rate", units="(Mbps)",
                tuple_list=host_stats.packet_sent_times)

            # Packet receive times.
            plt.subplot(4, 3, 6)
            rec_rate_lst = PlotTool.gen_rate_tuple_list(
                host_stats.packet_rec_times)
            PlotTool.graph_tuple_list(rec_rate_lst)
            receive_legend.append(host_addr)
            # Output average packet received per sec to log.
            PlotTool.output_rate_avg_tuple_list(
                id="Host " + host_addr,
                value_type="Receive Rate", units="(Mbps)",
                tuple_list=host_stats.packet_rec_times)

        # Finalize sent graph.
        plt.subplot(4, 3, 3)
        plt.legend(sent_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Host Send Rate (Mbps)")

        # Finalize receive graph.
        plt.subplot(4, 3, 6)
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
        fig.set_facecolor("white")

        # Figure adjust to window size.
        fig.set_size_inches(35, 10.5, forward=True)

        # Graph all three devices.
        self.graph_links()
        self.graph_flows()
        self.graph_hosts()

        # Make spacing between plots.
        plt.tight_layout()
        plt.show()