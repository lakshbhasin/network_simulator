"""This module contains all device definitions.
"""

from .common import *

class Device(object):
    """Representation of a device (Host or Router).

    :ivar str address: address of this device.
    """
    def __init__(self, address=None):
        self.address = address

    def __eq__(self, other):
        return self.address == other.address

    def __neq__(self, other):
        return not __eq__(self, other)

    # TODO(team): More event subclasses to come?