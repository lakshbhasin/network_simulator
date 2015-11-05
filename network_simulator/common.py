"""
This file contains definition of constants.
"""

"""Size of :class:`.AckPacket` is 512 bits."""
ACK_PACKET_SIZE_BITS = 512

"""Size of :class:`.DataPacket` is 8192 bits."""
DATA_PACKET_SIZE_BITS = 8192

"""Size of :class:`.RouterPacket` is 512 bits."""
ROUTER_PACKET_SIZE_BITS = 512

"""Initial window size for :class:`.Flow`, in packets."""
INITIAL_WINDOW_SIZE_PACKETS = 1

"""Initial router packet id of :class:`.RouterPacket` is -1."""
ROUTER_PACKET_DEFAULT_ID = -1

"""Flow's packet timeout limit in seconds."""
# TODO(team): What should this number be?
FLOW_TIMEOUT_SEC = 1

# TODO(team): In our doc we have, "hard code a constant
# to use new routing table after some time delay" in our
# old_routing_table field for Router class.