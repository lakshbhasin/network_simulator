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
the new routing table is considered stabilized and ready to use. This
estimate is somewhat conservative (for Test Case 1 TCP Reno, the router
stabilization only takes around 0.02 s)."""
ROUTING_TABLE_STAB_TIME_SEC = 0.15

"""Time (sec) between routing table updates. Must be long enough to ensure
convergence, but short enough to ensure routing is optimal."""
ROUTING_TABLE_UPDATE_PERIOD = 5.0

"""Initial window size for :class:`.Flow`, in packets."""
INITIAL_WINDOW_SIZE_PACKETS = 1.0

"""Initial router packet id of :class:`.RouterPacket` is -1."""
ROUTER_PACKET_DEFAULT_ID = -1

"""Conversion to/from bits <-> KB, MB"""
KILOBYTE = 8.0 * 1024
MEGABYTE = 1024 * KILOBYTE
MEGABIT = 128 * KILOBYTE

"""Flow's packet timeout limit in seconds."""
FLOW_TIMEOUT_SEC = 0.5

"""
TCP FAST window update smoothing parameter "gamma" (see
http://netlab.caltech.edu/publications/FAST-ToN-final-060209-2007.pdf)
"""
TCP_FAST_DEFAULT_GAMMA = 0.5

"""
TCP FAST baseRTT/RTT additive smoothing parameter "alpha" (see above FAST paper)
"""
TCP_FAST_DEFAULT_ALPHA = 2.0

"""
TCP FAST time period (sec) for window updates.
"""
TCP_FAST_UPDATE_PERIOD_SEC = 0.05

"""
Default max number of packets to average in computing RTTs for TCP algorithms.
"""
TCP_NUM_PACKETS_AVE_FOR_RTT = 40

"""
Default initial slow start threshold (in packets) for TCP algorithms.
"""
TCP_INITIAL_SS_THRESH = 100.0

"""
Window size in time interval for graphing in seconds.
"""
GRAPH_WINDOW_SIZE = 0.10

"""
If non-None, this is a list of the Links for which we want to see stats. This
is used to reduce visual clutter (especially in Test Cases 1-2).
"""
LINKS_TO_CALC_STATS = None

"""
Buffer occupancies use a different window size (in seconds) for their graph
since they change more often.
"""
BUFFER_OCC_WINDOW_SIZE = 0.05
