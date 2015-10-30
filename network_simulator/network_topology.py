"""
Module for NetworkTopology class.
"""

import copy
import json
from Queue import Queue

from .host import *
from .common import *
from .router import *

import jsonpickle

class NetworkTopology(object):
    """
    A wrapper class that contains a list of Links, Hosts, Routers, and Flows.
    This is only used for setting up the topology (or writing it to file),
    and should not be used to track global state. This object will be serialized
    and written out as JSON.

    Note that Hosts and Routers should not have their Link attributes set
    when loaded in from file; these will be set later to make sure the same
    reference is used (as JSON cannot easily record references). Similarly,
    Links should just have addresses specified for their two ends; Devices
    will be set up later.
    """

    def __init__(self, links=None, flows=None, hosts=None, routers=None):
        """
        :ivar list<Link> links
        :ivar list<Host> hosts
        :ivar list<Flow> flows
        :ivar list<Router> routers
        """
        self.links = links
        self.hosts = hosts
        self.flows = flows
        self.routers = routers

    @staticmethod
    def init_from_json_file(json_file_name):
        """
        Initializes and returns a NetworkTopology object. This involves
        reading in from JSON, making sure the topology passes some
        preconditions, connecting up the Routers' and Hosts' Links and other
        properties, etc.
        :param json_file_name: the JSON file describing the NetworkTopology
        :return: the constructed, fully-initialized NetworkTopology
        """
        with open(json_file_name, 'r') as fin:
            topology_json_str = fin.read()
            topology = jsonpickle.decode(topology_json_str)

            topology.check_preconditions()
            topology.complete_initialization()

        return topology

    def write_to_json(self, json_file_name):
        """
        A convenience function that writes this NetworkTopology to JSON in a
        readable format. The topology's preconditions are first checked
        before it is written. Usage (in Python shell):
            > topology = NetworkToplogy()
            > # set links, hosts, flows, routers
            > topology.write_to_json("./test.json")

        :param json_file_name: the JSON file that will hold the topology
        """
        self.check_preconditions()

        topology_json = jsonpickle.encode(self)
        topology_json_pretty = json.dumps(json.loads(topology_json), indent=4)
        with open(json_file_name, 'w') as fout:
            fout.write(topology_json_pretty)

    def check_preconditions(self):
        """
        Checks some preconditions on the NetworkTopology object, and throws a
        ValueError if these are not met. In addition to checking that all of
        the required attributes are set, the following additional checks are
        carried out:
            1) A Router cannot have its "links" attribute set.
            2) A Host cannot have its "link" attribute set.
            3) Device addresses must be unique.
            4) A Link should have its "end_1_addr" and "end_2_addr" set,
            but not the actual Devices themselves.
            5) (end_1_addr, end_2_addr) must uniquely identify a Link.
            6) Links must have a buffer size set in their LinkBuffer, but no
            other params set for the LinkBuffer.
            7) Flows must have a source and destination addresses set,
            and these must correspond to Hosts. But no actual Host references
            should be connected to the Flows yet.
            8) Flows must have unique IDs.
        """
        # Note: it's possible to have no Routers in a network.
        if self.hosts is None:
            raise ValueError("Hosts were not specified in input JSON")

        if self.links is None:
            raise ValueError("Links were not specified in input JSON")

        if self.flows is None:
            raise ValueError("Flows were not specified in input JSON")

        # Check for unique Device addresses, and track Host addresses
        device_addrs = set()
        host_addrs = set()

        for rout in self.routers:
            if rout.links is not None:
                raise ValueError("Router " + rout + " in input JSON had "
                                 "non-None links")
            if rout.address is None:
                raise ValueError("Router " + rout + " in input JSON did not "
                                 "have required properties set")

            if rout.address in device_addrs:
                raise ValueError("Router " + rout + " had same address as "
                                 "another Device")
            else:
                device_addrs.add(rout.address)

        for host in self.hosts:
            if host.link is not None:
                raise ValueError("Host " + host + " in input JSON had non-None"
                                 " link")
            if host.address is None:
                raise ValueError("Host " + host + " in input JSON did not have"
                                 " required properties set")

            if host.address in device_addrs:
                raise ValueError("Host " + host + " had same address as another"
                                 " Device")
            else:
                device_addrs.add(host.address)
                host_addrs.add(host.address)

        # Check that set(end_1_addr, end_2_addr) is always unique, regardless
        # of order
        link_ends = set()
        for link in self.links:
            if link.end_1_addr is None or link.end_2_addr is None \
                    or link.static_delay_sec is None \
                    or link.capacity_bps is None \
                    or link.buffer is None \
                    or link.buffer.buffer_size_bits is None:
                raise ValueError("Link " + link + " did not have required "
                                 "properties set")
            if link.end_1_device is not None or link.end_2_device is not None:
                raise ValueError("Ends of Link " + link + " had Devices set")
            if link.buffer.queue is not None:
                raise ValueError("Link buffer " + link.buffer + " of Link "
                                 + link + "had non-required properties set")

            if {link.end_1_addr, link.end_2_addr} in link_ends:
                raise ValueError("Link " + link + " had same ends as another "
                                 "Link.")
            else:
                link_ends.add({link.end_1_addr, link.end_2_addr})

        # Check for unique Flow IDs
        flow_ids = set()
        for flow in self.flows:
            if flow.source_addr is None or flow.dest_addr is None or \
                    flow.id is None or flow.data_size_bits is None or \
                    flow.start_time is None:
                raise ValueError("Flow " + flow + " did not have required "
                                 "properties")
            if flow.source is not None or flow.dest is not None:
                raise ValueError("Flow " + flow + " had a source or dest "
                                 "Device set.")
            if flow.source_addr not in host_addrs or \
                    flow.dest_addr not in host_addrs:
                raise ValueError("Flow " + flow + " had non-Host source or "
                                 "destination address")

            if flow.id in flow_ids:
                raise ValueError("Flow " + flow + " had same ID as another "
                                 "Flow.")
            else:
                flow_ids.add(flow.id)

    def __get_device_with_addr(self, device_addr):
        devices = copy.copy(self.hosts)
        devices.append(self.routers)
        for device in devices:
            if device.address == device_addr:
                return device

        return None

    def __get_host_with_addr(self, host_addr):
        # Host address should be unique among Devices
        host = self.__get_device_with_addr(host_addr)
        if host is not None and not isinstance(host, Host):
            raise ValueError("Tried to get Host with address " + host_addr +
                             ", but instead got non-Host " + str(host))
        return host

    def __get_router_with_addr(self, router_addr):
        # Router address should be unique among Devices
        router = self.__get_device_with_addr(router_addr)
        if router is not None and not isinstance(router, Router):
            raise ValueError("Tried to get Router with address " +
                             router_addr + ", but instead got non-Router " +
                             str(router))
        return router

    def __get_links_with_end_addr(self, end_addr):
        """
        :param end_addr: the Device address of interest
        :return: list of Links that contain a given Device on one end.
        """
        desired_links = []
        for link in self.links:
            if link.end_1_addr == end_addr or link.end_2_addr == end_addr:
                desired_links.append(link)

        return desired_links

    def __get_flows_with_source_addr(self, source_addr):
        """
        :param source_addr: the Host address of the source
        :return: list of Flows that start at the given Host.
        """
        desired_flows = []
        for flow in self.flows:
            if flow.source_addr == source_addr:
                desired_flows.append(flow)

        return desired_flows

    def complete_initialization(self):
        """
        Completes initialization of Links, Hosts, Flows, and Routers for this
        topology, by creating required attributes and connecting together all
        of the components via references.

        This is also where the Router and Host get their link/links attributes
        set.
        """
        # Set up un-initialized Host attributes
        for host in self.hosts:
            host.flow_packets_received = dict()

            # Get Link connected to this Host.
            connected_links = self.__get_links_with_end_addr(host.address)
            if len(connected_links) > 1:
                raise ValueError("Host " + host + " had more than one "
                                 "connected Link.")
            if len(connected_links) == 0:
                host.link = None
            else:
                host.link = connected_links[0]

            # Configure Flows that start at this Host.
            connected_flows = self.__get_flows_with_source_addr(host.address)
            flows_dict = dict()
            for flow in connected_flows:
                flows_dict[flow.id] = flow
            host.flows = flows_dict

        # Set up un-initialized Router attributes
        for router in self.routers:
            router.routing_table = dict()
            router.old_routing_table = dict()
            router.device_distances = dict()

            router.links = self.__get_links_with_end_addr(router.address)

        # Set up un-initialized Link attributes
        for link in self.links:
            link.end_1_device = self.__get_device_with_addr(link.end_1_addr)
            link.end_2_device = self.__get_device_with_addr(link.end_2_addr)
            link.buffer.queue = Queue()

        # Set up un-initialized Flow attributes
        for flow in self.flows:
            flow.source = self.__get_host_with_addr(flow.source_addr)
            flow.dest = self.__get_host_with_addr(flow.dest_addr)
            flow.window_size_packets = INITIAL_WINDOW_SIZE_PACKETS
            flow.packets_in_transit = list()
            flow.packet_rtts = list()

            # TODO(team): Set up other initial params depending on the Flow's
            # TCP algorithm (i.e. the subclass)? Could also just pass these
            # into the JSON.
