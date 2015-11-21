"""This module contains Router definition.
"""

import logging

from common import *
from device import Device
from event import Event
from packet import AckPacket, DataPacket, RouterPacket

logger = logging.getLogger(__name__)


class Router(Device):
    """Representation of a router.
    A router routes :class:`Packets <.Packet>` through the network to their
    destinations, which are :class:`Hosts <.Host>`.

    :ivar dict new_routing_table: the newest routing table hashmap, from Host
        ID (string) to a connected :class:`Link <.Link>`. This may be in the
        process of construction and is hence not stable.
    :ivar dict stable_routing_table: a stable routing table, i.e. an archived
        version from a previous update event.
    :ivar dict self_to_neighb_dists: a hashmap from a neighboring Device to
        the cost to travel from self to that neighbor (in sec).
    :ivar dict neighb_to_host_dists: a hashmap from RouterHost objects to the
        *min* cost to travel between the given Router and Host (in sec). The
        Routers in this must be direct neighbors of this Router.
    :ivar dict self_to_host_dists: a hashmap from Hosts to the *min* cost to
        travel between this Router and that Host (in sec). The Host may not
        be directly connected. This is what is passed on (in a transformed
        form) during RouterPacket creation.
    :ivar list links: all :class:`Links <.Link>` connected to this
        :class:`.Router`.
    :ivar float last_table_update_timestamp: timestamp (in sec) when the
        last routing table update was initiated.
    :ivar list neighbors: a list of Devices directly connected to this
        Router. This is assumed to not change over time (i.e. no destruction).
    """
    def __init__(self, address, links=None):
        Device.__init__(self, address)
        self.new_routing_table = dict()
        self.stable_routing_table = None
        self.neighb_to_host_dists = dict()
        self.self_to_host_dists = dict()
        self.links = links
        self.last_table_update_timestamp = 0.0
        self.neighbors = []
        self.self_to_neighb_dists = dict()

    def setup_neighbors(self):
        """
        This function is called after the NetworkTopology class has connected
        Links to this router. This is used to make sure the Router knows its
        neighbors.
        """
        # Compute neighbors based on links.
        neighbors = []
        assert self.links is not None
        for link in self.links:
            # Neighbor associated with Link (i.e. Device on the other side).
            neighbor = link.get_other_end(self)
            neighbors.append(neighbor)
        self.neighbors = neighbors

        # Update self --> neighbor distances based on connected Links,
        # and calculate initial routing table based on just this data.
        self.self_to_neighb_dists = dict()
        self.update_routing_table(global_clock_sec=0.0,  # assume time = 0.0
                                  update_self_to_neighbor_dists=True)

    def update_self_neighbor_dists(self, global_clock_sec):
        """
        Updates the distances from this Router to its neighbors, based on
        their link costs.
        :param: float global_clock_sec: The current time, used to make sure
        out-of-date queuing delay data is not used.
        """
        new_self_to_neighb_dists = dict()
        for link in self.links:
            # Neighbor associated with Link (i.e. Device on the other side).
            neighbor = link.get_other_end(self)
            new_self_to_neighb_dists[neighbor] = \
                link.get_link_cost(global_clock_sec)

        self.self_to_neighb_dists = new_self_to_neighb_dists

    def get_neighbor_routers(self):
        """
        :return: list of neighbors that are Routers.
        """
        neighbor_routers = []
        for device in self.neighbors:
            if isinstance(device, Router):
                neighbor_routers.append(device)

        return neighbor_routers

    def get_neighbor_hosts(self):
        """
        :return: list of neighbors that are Hosts.
        """
        from host import Host
        neighbor_hosts = []
        for device in self.neighbors:
            if isinstance(device, Host):
                neighbor_hosts.append(device)

        return neighbor_hosts

    def get_known_hosts(self):
        """
        Gets the known Hosts in the network by looking at direct neighbors
        and entries in neighb_to_host_dists.
        :return: list of known Hosts.
        """
        known_hosts = self.get_neighbor_hosts()  # directly-connected Hosts
        for router_host in self.neighb_to_host_dists:
            known_hosts.append(router_host.host)

        return known_hosts

    def get_link_with_neighbor(self, neighbor):
        """
        Returns the Link in self.links that contains the given neighbor on one
        end. There should only be one such Link.
        :param neighbor: connected Device of interest.
        :return: Link, or None if no such Link is found.
        """
        assert neighbor in self.neighbors
        for link in self.links:
            if link.end_1_device == neighbor or link.end_2_device == neighbor:
                return link

        return None

    def get_link_to_host_id(self, host_id, curr_timestamp):
        """
        Gets the Link to reach a given Host ID, or None if there is no such
        Link. This is done by looking up the appropriate routing table. The
        new_routing_table is used first, but only if the time since the
        routing table update is >= ROUTING_TABLE_STAB_TIME_SEC or the stable
        routing table is empty, and the desired "host_id" is present. Otherwise,
        use the stable one.

        :param string host_id: destination Host
        :param float curr_timestamp: the current time (sec), used to check
            for whether it's safe to use the new routing table.
        :return: Link to reach "host", or None if no such Link.
        """
        link_to_use = None
        time_since_last_update = curr_timestamp - \
            self.last_table_update_timestamp
        assert time_since_last_update >= 0.0

        if host_id in self.new_routing_table and \
                (time_since_last_update >= ROUTING_TABLE_STAB_TIME_SEC or
                 self.stable_routing_table is None or
                 len(self.stable_routing_table) == 0):
            link_to_use = self.new_routing_table[host_id]
        elif self.stable_routing_table is not None and \
                host_id in self.stable_routing_table:
            link_to_use = self.stable_routing_table[host_id]

        return link_to_use

    def update_routing_table(self, global_clock_sec,
                             update_self_to_neighbor_dists,
                             neighb_to_host_update=None):
        """
        A shortest-path (Bellman-Ford) function that recalculates the routing
        table based on a given neighb_to_host_dists update. This is called any
        time a RouterReceivedPacketEvent receives a RouterPacket. The
        self_to_host_dists map is updated to reflect the min cost between
        this Router and the known hosts. Return value indicates whether
        self_to_host_dists was updated.

        Postcondition: self.self_to_neighb_dists, self.neighb_to_host_dists,
        self.self_to_host_dists, and self.new_routing_table are updated (if
        necessary).

        :param float global_clock_sec: The current time in seconds (used to
        make sure that out-of-date queuing delay data is not used).
        :param bool update_self_to_neighbor_dists: whether to update
            self_to_neighb_dists. This should be set to True when a routing
            table update is initiated, but False otherwise (to prevent
            this method from continually returning True due to small queuing
            delay changes, and hence broadcasting more RouterPackets).
        :param dict neighb_to_host_update: a map from a RouterHost to the
            *min* distance between that Router and Host (in sec). The Router
            in the RouterHost must be a neighbor to this Router. If this is
            set to None, then only self --> neighbor Link cost updates are used.
        :return: True if self_to_host_dists was updated.
        """
        # Update self --> neighbor distances if desired.
        if update_self_to_neighbor_dists:
            self.update_self_neighbor_dists(global_clock_sec)

        # Update neighbor --> host distances based on incoming data (if any).
        if neighb_to_host_update is not None:
            for router_host, dist in neighb_to_host_update.iteritems():
                assert router_host.router in self.neighbors
                self.neighb_to_host_dists[router_host] = dist

        # Whether self.self_to_host_dists changed (assumed False initially).
        self_host_dists_changed = False

        known_hosts = self.get_known_hosts()
        for host in known_hosts:
            # Current next_link, and current {self -> host} cost.
            old_next_link = self.new_routing_table.get(host.address, None)
            old_self_to_host_min_dist = self.self_to_host_dists.get(
                host, float('inf'))

            new_next_neighbor = None  # new next neighbor to go towards
            new_self_to_host_min_dist = float('inf')

            # Minimize {self -> neighbor} + {neighbor -> host} dist,
            # and find the next hop and new {self -> host} dist.
            for neighbor in self.neighbors:
                router_to_host_dist = float('inf')
                if neighbor == host:
                    # This host must be in self_to_neighb_dists.
                    router_to_host_dist = self.self_to_neighb_dists[host]
                elif isinstance(neighbor, Router):
                    # Ignore non-Router neighbors that are not the
                    # destination Host. Cost is one-hop cost.
                    router_to_host_dist = \
                        self.self_to_neighb_dists[neighbor] + \
                        self.neighb_to_host_dists.get(
                            RouterHost(router=neighbor, host=host),
                            float('inf'))

                if router_to_host_dist < new_self_to_host_min_dist:
                    new_self_to_host_min_dist = router_to_host_dist
                    new_next_neighbor = neighbor

            # Update the self -> host distances.
            self.self_to_host_dists[host] = new_self_to_host_min_dist
            if new_self_to_host_min_dist != old_self_to_host_min_dist:
                self_host_dists_changed = True

            # Check if the next link for the routing table changed.
            new_next_link = self.get_link_with_neighbor(new_next_neighbor)
            if new_next_link != old_next_link:
                self.new_routing_table[host.address] = new_next_link

        return self_host_dists_changed

    def broadcast_router_packets(self, main_event_loop):
        """
        This function broadcasts RouterPackets to all of this Router's
        directly-connected Routers. The Packets hold self.self_to_host_dists
        (in a transformed form). Broadcasts are scheduled asynchronously.
        :param MainEventLoop main_event_loop: Event loop for scheduling
            DeviceToLinkEvents asynchronously.
        """
        logger.debug("Router %s broadcasting router packets.", self.address)

        # Map from RouterHost to *min* distance (in sec) between this Router
        # and that Host. This is just a transformation of self_to_host_dists.
        router_to_host_dists = dict()
        for host, dist in self.self_to_host_dists.iteritems():
            router_to_host_dists[RouterHost(router=self, host=host)] = dist

        # Schedule DeviceToLinkEvent for each connected Router.
        for link in self.links:
            destination = link.get_other_end(self)
            if not isinstance(destination, Router):
                continue

            router_packet = RouterPacket(source_id=self.address,
                                         dest_id=destination.address,
                                         start_time_sec=
                                         main_event_loop.global_clock_sec,
                                         router_to_host_dists=
                                         router_to_host_dists)
            from link import DeviceToLinkEvent
            dev_to_link_ev = DeviceToLinkEvent(packet=router_packet,
                                               link=link,
                                               dest_dev=destination)
            main_event_loop.schedule_event_with_delay(dev_to_link_ev, 0.0)


class RouterHost(object):
    """
    A wrapper class to hold a (Router, Host) tuple.
    """
    def __init__(self, router, host):
        """
        :ivar router
        :ivar host
        """
        self.router = router
        self.host = host

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.router == other.router and self.host == other.host

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.router) + hash(self.host)


class InitiateRoutingTableUpdateEvent(Event):
    """
    A periodically executing Event that initiates a routing table update.
    This just involves sending RouterPackets in order to calculate the
    distance between this Router and Hosts in the network.
    """

    def __init__(self, router):
        """
        :ivar Router router: the Router for which we're initiating a routing
        table update.
        :return:
        """
        Event.__init__(self)
        self.router = router

    def run(self, main_event_loop, statistics):
        """
        Initiates the routing table update by updating metadata and updating
        directly connected Links' costs.
        :param main_event_loop:
        :param statistics:
        """
        # Swap out the routing tables.
        self.router.stable_routing_table = self.router.new_routing_table
        self.router.new_routing_table = dict()

        # Mark routing table update time.
        self.router.last_table_update_timestamp = \
            main_event_loop.global_clock_sec

        # Trigger update based only on changed Link costs of the Router's
        # direct neighbors. This will set up self_to_host_dists properly.
        self.router.update_routing_table(
            global_clock_sec=main_event_loop.global_clock_sec,
            update_self_to_neighbor_dists=True)

    def schedule_new_events(self, main_event_loop):
        """
        Create a RouterPacket with the current self.router.self_to_host_dists
        (transformed appropriately) and send it down each connected Link via
        a DeviceToLinkEvent. Also, initiate another RouterReceivedPacketEvent.
        :param main_event_loop:
        """
        self.router.broadcast_router_packets(main_event_loop)

        # Schedule another InitiateRoutingTableUpdateEvent
        init_rt_upd_ev = InitiateRoutingTableUpdateEvent(self.router)
        main_event_loop.schedule_event_with_delay(init_rt_upd_ev,
                                                  ROUTING_TABLE_UPDATE_PERIOD)


class RouterReceivedPacketEvent(Event):
    """
    Handles the receipt of a Packet, which can be an ACK or data packet
    (handled equivalently) or a Router packet.
    """

    def __init__(self, router, packet):
        """
        :ivar Router router: the Router receiving the Packet
        :ivar Packet packet: Packet received
        :ivar Link link: (temporary) chosen Link for routing (for data/ACKs)
        :ivar bool router_to_host_dists_changed: whether the Router's
            "self_to_host_dists" changed. If so, additional RouterPackets must
            be broadcasted.
        """
        Event.__init__(self)
        self.router = router
        self.packet = packet
        self.link = None
        self.router_to_host_dists_changed = False

    def run(self, main_event_loop, statistics):
        """
        For data/ACKs: Looks up which Link to route through. If there is no
        route to the given Host, the packet is dropped.
        For router packets: Sanity checks, then update routing table
        synchronously.
        :param main_event_loop:
        :param statistics:
        """
        if isinstance(self.packet, DataPacket) or \
                isinstance(self.packet, AckPacket):
            self.link = self.router.get_link_to_host_id(
                host_id=self.packet.dest_id,
                curr_timestamp=main_event_loop.global_clock_sec)
            if self.link is None:
                # Drop Packet and inform statistics.
                logger.info("Router " + self.router.address + " could not " +
                            "route packet going to " + self.packet.dest_id)
                # TODO(team): Need way of detecting packet loss at Router?
                pass
        else:
            # Ensure RouterPacket's final destination was this Router.
            assert isinstance(self.packet, RouterPacket)
            assert self.packet.dest_id == self.router.address

            # Check if the Router's "self_to_host_dists" changed. Do not update
            # router --> neighbor direct distances on receipt of a RouterPacket,
            # since that will cause constant broadcasting of RouterPackets
            # (as "self_to_host_dists" keeps changing based on neighbors'
            # link costs).
            self.router_to_host_dists_changed = \
                self.router.update_routing_table(
                    global_clock_sec=main_event_loop.global_clock_sec,
                    update_self_to_neighbor_dists=False,
                    neighb_to_host_update=self.packet.router_to_host_dists)

    def schedule_new_events(self, main_event_loop):
        """
        For data/ACKs: Schedules a DeiceToLinkEvent if route was found.
        For router packets: Router sends its self_to_host_dists in the right
        format, to all of its connected Routers. But *only* if the Router's
        "self_to_host_dists" changed.
        :param main_event_loop:
        """
        if isinstance(self.packet, DataPacket) or \
                isinstance(self.packet, AckPacket):
            if self.link is not None:
                destination = self.link.get_other_end(self.router)
                from link import DeviceToLinkEvent
                dev_to_link_ev = DeviceToLinkEvent(packet=self.packet,
                                                   link=self.link,
                                                   dest_dev=destination)
                main_event_loop.schedule_event_with_delay(dev_to_link_ev, 0.0)
        else:
            assert isinstance(self.packet, RouterPacket)
            if self.router_to_host_dists_changed:
                self.router.broadcast_router_packets(main_event_loop)
