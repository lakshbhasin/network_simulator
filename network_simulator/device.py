"""This module contains all device definitions.

.. autosummary::
    Host
    Router
"""

# Imports go here.
# e.g.    from .common import ACK_PACKET_SIZE_BITS

class Device(object):
    """Representation of a device (Host or Router).

    :param str name: name of this device from the input file.
    :param str address: IP address of this device.
    :ivar str name: name of this device from the input file.
    :ivar str address: IP address of this device.
    """
    # TODO(team): Do we need a "name" here?
    def __init__(self, name=None, address=None):
        self.name = name
        self.address = address

    def __eq__(self, other):
        return self.address == other.address

    def __neq__(self, other):
        return not __neq__(self, other)

    # TODO(team): More event subclasses to come?

class Host(Device):
    """Representation of a host.
    A host sends :class:`Packets <.Packet>` through a :class:`.Link` to a
    :class:`.Router` or a :class:`.Host`.

    :param dict flows: :class:`Flows <.Flow>` from this :class:`.Host`.
    :param link: :class:`Link` connected to this :class:`.Host`.
    :ivar dict flows: :class:`Flows <.Flow>` from this :class:`.Host`.
    :ivar link: :class:`Link` connected to this :class:`.Host`.
    """
    def __init__(self, name=None, address=None, flows={}, link=None):
        Device.__init__(self, name, address)
        self.flows = flows
        self.link = link

    def __str__(self):
        return 'A host at IP address: ' + self.address

    # TODO(team): More event subclasses to come?

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
    def __init__(self, name=None, address=None, routing_table={},
                 old_routing_table={}, device_distances={}, links=[]):
        Device.__init__(self, name, address)
        self.routing_table = routing_table
        self.old_routing_table = old_routing_table
        self.device_distances = device_distances
        self.links = links

    def __str__(self):
        return 'A router at IP address: ' + self.address

    # TODO(team): More event subclasses to come.