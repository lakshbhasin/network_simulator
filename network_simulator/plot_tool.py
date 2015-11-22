import matplotlib.pyplot as plt
import numpy as np

from statistics import *

class PlotTool(object):
    """
    Produces graph of different data structures.
    """
    def __init__(self):
        pass

    def gen_rate_tuple_list(self, tuple_list):
        """
        Computes a tuple list of rates based on a (timestamp, data) tuple
        list.

        :param list tuple_list: list of tuples to be converted.
        :return: list
        """
        curr_count = 0
        curr_sum = 0
        curr_time = GRAPH_WINDOW_SIZE
        output = []
        for tup_idx in range(len(tuple_list)):
            timestamp, data = tuple_list[tup_idx]
            if timestamp > curr_time:
                if curr_count != 0:
                    output.append((curr_time, float(curr_sum) / curr_count))
                    curr_count = 0
                    curr_sum = 0
                curr_time += GRAPH_WINDOW_SIZE
            if timestamp <= curr_time:
                curr_count += 1
                curr_sum += data
        # Append the last elements if they did not reach an end of an
        # interval.
        if curr_count != 0:
            output.append((curr_time, float(curr_sum) / curr_count))
        return output

    def graph_tuple_list(self, tuple_list=[], scatter=False):
        """
        Graphs the content of a tuple list.

        :param list tuple_list: if we have a newer version of the list,
        we would like to replace the previous version.
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

    def graph_1d_list(self, lst=[]):
        """
        Graphs the content of a list.

        :param list lst: list of values for the 1-D graph.
        """
        if not lst:
            return

        # Plot 1-D different values on a x-y plane.
        plt.plot(lst, np.zeros_like(lst), marker='o', linestyle='--')

class Grapher(object):
    """
    Graphs statistics items from Statistics class.
    """
    def __init__(self, stats=None):
        """
        :ivar Statistics stats: input Statistics object for graphing.
        :ivar PlotTool tool: graphing functions.
        """
        self.stats = stats
        self.tool = PlotTool()

    def graph_links(self):
        """
        Graphs the link stats of each available link.
        """
        # Set up legend storage for link names.
        occpy_legend = []
        loss_legend = []
        trans_legend = []

        # Iterate through each link to display each stats.
        for link, link_stats in self.stats.link_stats.iteritems():
            # Name of link would be "link_name".
            # Buffer occupancy w.r.t time.
            plt.subplot(431)
            self.tool.graph_tuple_list(link_stats.buffer_occupancy)
            occpy_legend.append(link)

            # Packet loss times.
            plt.subplot(434)
            self.tool.graph_1d_list(link_stats.packet_loss_times)
            loss_legend.append(link)

            # Packet transmission w.r.t time.
            plt.subplot(437)
            self.tool.graph_tuple_list(link_stats.packet_transmit_times)
            trans_legend.append(link)

        # Finalize buffer occupancy graph.
        plt.subplot(431)
        plt.legend(occpy_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Buffer Occupancy (pkts)")
        # Set up grid on graph.
        plt.grid(True)

        # Finalize loss times graph.
        plt.subplot(434)
        plt.legend(loss_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Packet Loss Times")
        # Set up grid on graph.
        plt.grid(True)

        # Finalize packet transmission graph.
        plt.subplot(437)
        plt.legend(trans_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Size of Packet Transmitted (Bits)")
        # Set up grid on graph.
        plt.grid(True)

    def graph_flows(self):
        """
        Graphs the flow stats of each available flow.
        """
        # Set up legend storage for flow names.
        sent_legend = []
        receive_legend = []
        rtt_legend = []
        window_legend = []

        # Iterate through each flow to display each stats.
        for flow, flow_stats in self.stats.flow_stats.iteritems():
            # Name of flow would be "flow_id".
            # Packet sent times.
            plt.subplot(432)
            sent_rate_lst = self.tool.gen_rate_tuple_list(
                flow_stats.packet_sent_times)
            self.tool.graph_tuple_list(sent_rate_lst)
            sent_legend.append(flow)

            # Packet receive times.
            plt.subplot(435)
            rec_rate_lst = self.tool.gen_rate_tuple_list(
                flow_stats.packet_rec_times)
            self.tool.graph_tuple_list(rec_rate_lst)
            receive_legend.append(flow)

            # Packet RTT times.
            plt.subplot(438)
            self.tool.graph_1d_list(flow_stats.packet_rtts)
            rtt_legend.append(flow)

            # Window size in packets w.r.t time.
            plt.subplot(4,3,11)
            self.tool.graph_tuple_list(flow_stats.window_size_times)
            window_legend.append(flow)

        # Finalize sent graph.
        plt.subplot(432)
        plt.legend(sent_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Packet Sent Times")
        # Set up grid on graph.
        plt.grid(True)

        # Finalize receive graph.
        plt.subplot(435)
        plt.legend(receive_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Packet Received Times")
        # Set up grid on graph.
        plt.grid(True)

        # Finalize RTT graph.
        plt.subplot(438)
        plt.legend(rtt_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("RTT (sec)")
        # Set up grid on graph.
        plt.grid(True)

        # Finalize window size graph.
        plt.subplot(4,3,11)
        plt.legend(window_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Window Size (pkts)")
        # Set up grid on graph.
        plt.grid(True)

    def graph_hosts(self):
        """
        Graphs the host stats of each available host.
        """
        # Set up legend storage for host names.
        sent_legend = []
        receive_legend = []

        # Iterate through each host to display each stats.
        for host, host_stats in self.stats.host_stats.iteritems():
            # Name of host would be "host_address".
            # Packet sent times.
            plt.subplot(433)
            sent_rate_lst = self.tool.gen_rate_tuple_list(
                host_stats.packet_sent_times)
            self.tool.graph_tuple_list(sent_rate_lst)
            sent_legend.append(host)

            # Packet receive times.
            plt.subplot(436)
            rec_rate_lst = self.tool.gen_rate_tuple_list(
                host_stats.packet_rec_times)
            self.tool.graph_tuple_list(rec_rate_lst)
            receive_legend.append(host)

        # Finalize sent graph.
        plt.subplot(433)
        plt.legend(sent_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Packet Sent Times")
        # Set up grid on graph.
        plt.grid(True)

        # Finalize receive graph.
        plt.subplot(436)
        plt.legend(receive_legend)
        # Set up labels.
        plt.xlabel("Time (sec)")
        plt.ylabel("Packet Received Times")
        # Set up grid on graph.
        plt.grid(True)

    def graph_network(self):
        """
        Graphs the entire network (this includes all links, flows, and hosts.
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
        #plt.axis('equal')
        plt.show()