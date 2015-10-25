"""This file contains definition of constants.
"""

"""Size of :class:`.AckPacket` is 512 bits."""
ACK_PACKET_SIZE_BITS = 512

"""Size of :class:`.DataPacket` is 8192 bits."""
DATA_PACKET_SIZE_BITS = 8192

"""Size of :class:`.RouterPacket` is 512 bits."""
ROUTER_PACKET_SIZE_BITS = 512

# TODO(team): In our doc we have, "hard code a constant
# to use new routing table after some time delay" in our
# old_routing_table field for Router class.