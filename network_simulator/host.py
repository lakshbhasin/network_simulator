"""This module contains all Host definition.
"""

from .device import *

class Host(Device):
    """Representation of a host.
    A host sends :class:`Packets <.Packet>` through a :class:`.Link` to a
    :class:`.Router` or a :class:`.Host`.

    :ivar dict flows: :class:`Flows <.Flow>` from this :class:`.Host`.
    :ivar link: :class:`Link` connected to this :class:`.Host`.
    """
    def __init__(self, address=None, flows={}, link=None):
        Device.__init__(self, address)
        self.flows = flows
        self.link = link

    def __repr__(self):
        return 'A host at address: ' + self.address

    # TODO(team): More event subclasses to come?