"""This module contains Router definition.
"""

from .device import *


class Router(Device):
    """Representation of a router.
    A router routes :class:`Packets <.Packet>` through the network to their
    destinations, which are :class:`Hosts <.Host>`.

    :ivar dict routing_table: a routing table hashmap from Host to connected
        :class:`Links <.Link>`.
    :ivar dict old_routing_table: same as routing_table, except this is an
        archived version from previous update event (wait until next update
        event to repeat).
    :ivar dict device_distances: a hashmap from (:class:`.Device`,
        :class:`.Device`) sets to the cost to travel between those two
        :class:`Devices <.Device>` (in seconds).
    :ivar list links: all :class:`Links <.Link>` connected to this
        :class:`.Router`.
    """
    def __init__(self, address=None, routing_table={},
                 old_routing_table={}, device_distances={}, links=[]):
        Device.__init__(self, address)
        self.routing_table = routing_table
        self.old_routing_table = old_routing_table
        self.device_distances = device_distances
        self.links = links

    # TODO(team): More event subclasses to come.