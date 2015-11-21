import matplotlib.pyplot as plt
import numpy as np

from statistics import *

class PlotTool(object):
    """
    Produces graph of different data structures.
    """
    def __init__(self):
        pass

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

    def graph_links(self, dct):
        """
        Graphs the link stats of each available link.
        """
        # TODO(sharon): Remove dct as input once we are done with PR.
        # Set up legend storage for link names.
        occpy_legend = []
        loss_legend = []
        trans_legend = []

        # Iterate through each link to display each stats.
        #for link, link_stats in self.stats.link_stats.iteritems():
        for link, link_stats in dct.iteritems():
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
        plt.xlabel("Time (Sec)")
        plt.ylabel("Buffer Occupancy (Count)")
        # Set up grid on graph.
        plt.grid(True)

        # Finalize loss times graph.
        plt.subplot(434)
        plt.legend(loss_legend)
        # Set up labels.
        plt.xlabel("Time (Sec)")
        plt.ylabel("Packet Loss Times")
        # Set up grid on graph.
        plt.grid(True)

        # Finalize packet transmission graph.
        plt.subplot(437)
        plt.legend(trans_legend)
        # Set up labels.
        plt.xlabel("Time (Sec)")
        plt.ylabel("Size of Packet Transmitted (Bits)")
        # Set up grid on graph.
        plt.grid(True)

    def graph_flows(self, dct):
        """
        Graphs the flow stats of each available flow.
        """
        # TODO(sharon): Remove dct as input once we are done with PR.
        # Set up legend storage for flow names.
        sent_legend = []
        receive_legend = []
        rtt_legend = []
        window_legend = []

        # Iterate through each flow to display each stats.
        #for flow, flow_stats in self.stats.flow_stats.iteritems():
        for flow, flow_stats in dct.iteritems():
            # Name of flow would be "Flow flow_id".
            flow_name = "Flow " + flow

            # Packet sent times.
            plt.subplot(432)
            self.tool.graph_1d_list(host_stats.packet_sent_times)
            sent_legend.append(flow_name)

            # Packet receive times.
            plt.subplot(435)
            self.tool.graph_1d_list(host_stats.packet_rec_times)
            receive_legend.append(flow_name)

            # Packet RTT times.
            plt.subplot(438)
            self.tool.graph_1d_list(flow_stats.packet_rtts)
            rtt_legend.append(flow_name)

            # Window size in packets w.r.t time.
            plt.subplot(4,3,11)
            self.tool.graph_tuple_list(flow_stats.window_size_times)
            window_legend.append(flow_name)

        # Finalize sent graph.
        plt.subplot(432)
        plt.legend(sent_legend)
        # Set up labels.
        plt.xlabel("Time (Sec)")
        plt.ylabel("Packet Sent Times")
        # Set up grid on graph.
        plt.grid(True)

        # Finalize receive graph.
        plt.subplot(435)
        plt.legend(receive_legend)
        # Set up labels.
        plt.xlabel("Time (Sec)")
        plt.ylabel("Packet Received Times")
        # Set up grid on graph.
        plt.grid(True)

        # Finalize RTT graph.
        plt.subplot(438)
        plt.legend(rtt_legend)
        # Set up labels.
        plt.xlabel("Time (Sec)")
        plt.ylabel("RTT")
        # Set up grid on graph.
        plt.grid(True)

        # Finalize window size graph.
        plt.subplot(4,3,11)
        plt.legend(window_legend)
        # Set up labels.
        plt.xlabel("Time (Sec)")
        plt.ylabel("Window Size (# of Packets)")
        # Set up grid on graph.
        plt.grid(True)

    def graph_hosts(self, dct):
        """
        Graphs the host stats of each available host.
        """
        # TODO(sharon): Remove dct as input once we are done with PR.
        # Set up legend storage for host names.
        sent_legend = []
        receive_legend = []

        # Iterate through each host to display each stats.
        #for host, host_stats in self.stats.host_stats.iteritems():
        for host, host_stats in dct.iteritems():
            # Name of host would be "host_address".
            # Packet sent times.
            plt.subplot(433)
            self.tool.graph_1d_list(host_stats.packet_sent_times)
            sent_legend.append(host)

            # Packet receive times.
            plt.subplot(436)
            self.tool.graph_1d_list(host_stats.packet_rec_times)
            receive_legend.append(host)

        # Finalize sent graph.
        plt.subplot(433)
        plt.legend(sent_legend)
        # Set up labels.
        plt.xlabel("Time (Sec)")
        plt.ylabel("Packet Sent Times")
        # Set up grid on graph.
        plt.grid(True)

        # Finalize receive graph.
        plt.subplot(436)
        plt.legend(receive_legend)
        # Set up labels.
        plt.xlabel("Time (Sec)")
        plt.ylabel("Packet Received Times")
        # Set up grid on graph.
        plt.grid(True)

    def graph_network(self, dct1, dct2, dct3):
        """
        Graphs the entire network (this includes all links, flows, and hosts.
        """
        # TODO(sharon): Remove dct as input once we are done with PR.
        # Set up matplotlib window name.
        fig = plt.figure()
        fig.canvas.set_window_title("Network Statistics")

        # Figure adjust to window size.
        fig.set_size_inches(35, 10.5, forward=True)

        # Graph all three devices.
        # TODO(sharon): Remove dct as input once we are done with PR.
        self.graph_links(dct1)
        self.graph_flows(dct2)
        self.graph_hosts(dct3)

        # Make spacing between plots.
        plt.tight_layout()
        plt.axis('equal')
        plt.show()

# Plot examples.
# TODO(sharon): Remove these once PR is about to merge.
test = Grapher()

host_stats = HostStats()
host_stats.packet_sent_times = [1, 3, 5, 7, 10]
host_stats.packet_rec_times = [2, 3, 4, 5, 6]
host_stats2 = HostStats()
host_stats2.packet_sent_times = [1.5, 3, 3.5, 4]
host_stats2.packet_rec_times = [1.5, 2.5, 3.5, 4.5]
dct = {"hostaddr1": host_stats, "hostaddr2": host_stats2}

flow_stats = FlowStats()
flow_stats.packet_sent_times = [1, 3, 5, 7, 10]
flow_stats.packet_rec_times = [2, 3, 4, 5, 6]
flow_stats.packet_rtts = [3.5, 3.2, 2.5, 7.0]
flow_stats.window_size_times = [(0., 1), (1., 3), (2., 5)]
flow_stats2 = FlowStats()
flow_stats2.packet_sent_times = [1.5, 3, 3.5, 4]
flow_stats2.packet_rec_times = [1.5, 2.5, 3.5, 4.5]
flow_stats2.packet_rtts = [3., 2., 1.5, 2.5]
flow_stats2.window_size_times = [(0.5, 3), (1.5, 2), (2.5, 6)]
dct2 = {"flow_id1": flow_stats, "flow_id2": flow_stats2}

link_stats = LinkStats()
link_stats.buffer_occupancy = [(1.0, 4), (2.5, 7), (3.5, 4)]
link_stats.packet_loss_times = [2, 3, 4, 5, 6]
link_stats.packet_transmit_times = [(0.5, 2.2), (1.5, 3.2), (2.5, 2)]
link_stats2 = LinkStats()
link_stats2.buffer_occupancy = [(0.5, 2), (1.5, 3), (2.5, 2)]
link_stats2.packet_loss_times = [1.5, 2.5, 3.5, 4.5]
link_stats2.packet_transmit_times = [(1.5, 3), (2.5, 4), (3.5, 2.2)]
dct3 = {"(addr1, addr2)": link_stats, "(addr3, addr4)": link_stats2}

test.graph_network(dct3, dct2, dct)