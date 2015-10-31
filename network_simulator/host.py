"""This module contains all Host definition.
"""

from device import *


class Host(Device):
    """
    Representation of a host.
    A host sends :class:`Packets <.Packet>` through a :class:`.Link` to a
    :class:`.Router` or a :class:`.Host`.

    :ivar dict flows: :class:`Flows <.Flow>` from this :class:`.Host`.
    :ivar link: :class:`Link` connected to this :class:`.Host`.
    :ivar flow_packets_received: a map from flow ID to a sorted list of the
    packet IDs that have been received for that Flow. This is used to carry
    out "selective repeat" instead of "go-back-N".
    """
    def __init__(self, address=None, flows={}, flow_packets_received={},
                 link=None):
        Device.__init__(self, address)
        self.flows = flows
        self.flow_packets_received = flow_packets_received
        self.link = link

    # TODO(team): More event subclasses to come?