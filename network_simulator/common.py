"""
This file contains definition of constants.
"""

"""Size of :class:`.AckPacket` is 512 bits."""
ACK_PACKET_SIZE_BITS = 512

"""Size of :class:`.DataPacket` is 8192 bits."""
DATA_PACKET_SIZE_BITS = 8192

"""Size of :class:`.RouterPacket` is 512 bits."""
ROUTER_PACKET_SIZE_BITS = 512

"""Time (sec) after an "initiate routing table update event", after which
the new routing table is considered stabilized and ready to use."""
ROUTING_TABLE_STAB_TIME_SEC = 0.5

"""Time (sec) between routing table updates. Must be long enough to ensure
convergence, but short enough to ensure routing is optimal."""
ROUTING_TABLE_UPDATE_PERIOD = 5.0

"""Initial window size for :class:`.Flow`, in packets."""
INITIAL_WINDOW_SIZE_PACKETS = 1

"""Initial router packet id of :class:`.RouterPacket` is -1."""
ROUTER_PACKET_DEFAULT_ID = -1

"""Flow's packet timeout limit in seconds."""
# TODO(team): What should this number be?
FLOW_TIMEOUT_SEC = 1