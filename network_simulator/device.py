"""This module contains all device definitions.
"""


class Device(object):
    """Representation of a device (Host or Router).

    :ivar str address: address of this device.
    """
    def __init__(self, address):
        self.address = address

    def __hash__(self):
        return hash(self.address)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.address == other.address

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return str(self.__dict__)

    # TODO(team): More event subclasses to come?
