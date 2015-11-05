import matplotlib.pyplot as plt

class PlotTool(object):
    def __init__(self, tuple_list=[], title="Untitled Graph",
                 x_label="X-Axis", y_label="Y-Axis"):
        """
        Plot tool class to graph a tuple list.

        # TODO(sharon): Enable other types of data structures to be passed
        # into this class.

        :ivar list tuple_list: input data point as a list of tuples.
        :ivar string title: title of graph.
        :ivar string x_label: title of x-axis.
        :ivar string y_label: title of y-axis.
        """
        self.tuple_list = tuple_list
        self.title = title
        self.x_label = x_label
        self.y_label = y_label

    def graph(self, scatter=False):
        """
        Graph the content of the tuple list.

        :param boolean scatter: if we want a scatter plot, we set this
        variable to True; otherwise, it would be a line graph.
        """
        if scatter:
            # Scatter plot.
            plt.scatter(*zip(*self.tuple_list))
        else:
            # Line graph
            plt.plot(*zip(*self.tuple_list))

        # Set up title and labels.
        plt.title(self.title)
        plt.xlabel(self.x_label)
        plt.ylabel(self.y_label)
        # Set up grid on graph.
        plt.grid(True)
        plt.show()

# Testing
test = PlotTool([(1,1), (2,2), (3,3)], "My Graph", "Time", "People")
test.graph(True)