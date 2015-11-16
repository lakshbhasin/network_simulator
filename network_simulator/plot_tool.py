import matplotlib.pyplot as plt
import numpy as np

from statistics import *

class PlotTool(object):
    """
    Produces graph of different data structures.
    """
    def __init__(self):
        pass

    def graph_tuple_list(self, title="Untitled Graph",
                         x_label="X-Axis", y_label="Y-Axis",
                         tuple_list=[], scatter=False):
        """
        Graph the content of a tuple list.

        :param string title: title of graph.
        :param string x_label: title of x-axis.
        :param string y_label: title of y-axis.
        :param list tuple_list: if we have a newer version of the list,
        we would like to replace the previous version.
        :param boolean scatter: if we want a scatter plot, we set this
        variable to True; otherwise, it would be a line graph.
        """
        if tuple_list:
            tuple_list = tuple_list
        if scatter:
            # Scatter plot.
            plt.scatter(*zip(*tuple_list))
        else:
            # Line graph
            plt.plot(*zip(*tuple_list))

        # Set up title and labels.
        plt.title(title)
        plt.xlabel(x_label)
        plt.ylabel(y_label)

        # Set up grid on graph.
        plt.grid(True)

    def graph_1d_list(self, title="Untitled Graph",
                      x_label="X-Axis", y_label="Y-Axis", lst=[]):
        """
        Graph the content of a list.

        :param string title: title of graph.
        :param string x_label: title of x-axis.
        :param string y_label: title of y-axis.
        :param list lst: list of values for the 1-D graph.
        """
        # Plot 1-D different values on a x-y plane.
        plt.plot(lst, np.zeros_like(lst), 'o')

        # Set up title and labels.
        plt.title(title)
        plt.xlabel(x_label)
        plt.ylabel(y_label)

        # Set up grid on graph.
        plt.grid(True)


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

    def graph_link(self, link):
        """
        Graphs the link stats of a link.

        :param Link link: the link object to be graphed.
        """
        link_stats = self.stats.get_link_stats(link)

        # Name of link would be "Link (addr_1, addr_2)".
        link_name = "Link (" + link.end_1_addr + ", " + \
                    link.end_2_addr + ")"

        # Set up matplotlib window name.
        fig = plt.figure()
        fig.canvas.set_window_title(link_name)

        # Graph buffer occupancy.
        buf_title = "Buffer Occupancy for " + link_name
        plt.subplot(311)
        self.tool.graph_tuple_list(buf_title, "Global Time (Float)",
                                   "Buffer Occupancy",
                                   link_stats.buffer_occupancy, False)

        # Packet loss times.
        loss_title = "Buffer Loss Times for " + link_name
        plt.subplot(312)
        self.graph_1d_list(loss_title, "Global Time (Float)",
                           "", link_stats.packet_loss_times)

        # Graph packet transmission.
        trans_title = "Packet Transmit Times for " + link_name
        plt.subplot(313)
        self.graph_tuple_list(
            trans_title, "Global Time (Float)", "Packet Size (Bits)",
            link_stats.packet_transmit_times, False)

        # Proper spacing and display.
        plt.tight_layout()
        plt.axis('equal')
        plt.show()

    def graph_flow(self, flow):
        """
        Graphs the flow stats of a flow.

        :param Flow flow: the flow object to be graphed.
        """
        flow_stats = self.stats.get_flow_stats(flow)

        # Name of flow would be "Flow flow_id".
        flow_name = "Flow " + flow.flow_id

        # Set up matplotlib window name.
        fig = plt.figure()
        fig.canvas.set_window_title(flow_name)

        # Packet sent times.
        sent_title = "Packet Sent Times for " + flow_name
        plt.subplot(311)
        self.graph_1d_list(sent_title, "Global Time (Float)",
                           "", flow_stats.packet_sent_times)

        # Packet receive times.
        receive_title = "Packet Received Times for " + flow_name
        plt.subplot(312)
        self.graph_1d_list(receive_title, "Global Time (Float)",
                           "", flow_stats.packet_rec_times)

        # Packet RTT times.
        rtt_title = "Packet RTT for " + flow_name
        plt.subplot(313)
        self.graph_1d_list(rtt_title, "Global Time (Float)",
                           "", flow_stats.packet_rtts)

        # Proper spacing and display.
        plt.tight_layout()
        plt.axis('equal')
        plt.show()

    def graph_host(self, host):
        """
        Graphs the host stats of a host.

        :param Host host: the host object to be graphed.
        """
        host_stats = self.stats.get_host_stats(host)

        # Name of link would be "Host host_address".
        host_name = "Host " + host.address

        # Set up matplotlib window name.
        fig = plt.figure()
        fig.canvas.set_window_title(host_name)

        # Packet sent times.
        sent_title = "Packet Sent Times for " + host_name
        plt.subplot(211)
        self.graph_1d_list(sent_title, "Global Time (Float)",
                           "", host_stats.packet_sent_times)

        # Packet receive times.
        receive_title = "Packet Received Times for " + host_name
        plt.subplot(212)
        self.graph_1d_list(receive_title, "Global Time (Float)",
                           "", host_stats.packet_rec_times)

        # Proper spacing and display.
        plt.tight_layout()
        plt.axis('equal')
        plt.show()