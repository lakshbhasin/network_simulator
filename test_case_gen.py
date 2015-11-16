"""
Generates Test Cases 0, 1 and saves them to json
"""
from network_simulator.network_topology import *
from network_simulator.host import *
from network_simulator.common import *
from network_simulator.router import *
from network_simulator.flow import *
from network_simulator.link import *

if __name__ == "__main__":
    # test case 0
    links = list()
    l1 = Link("H1", "H2", h1, h2, LinkBuffer(64 * KILOBYTE), 0.01,
              10 * KILOBYTE, False)
    links.append(l1)
    h1.link = l1
    h2.link = l1

    hosts = list()
    h1 = Host("H1")
    h2 = Host("H2")
    hosts.append(h1)
    hosts.append(h2)

    # generate for FlowDummy
    flows = list()
    f1 = FlowDummy("F1", "H1", "H2", h1, h2, INITIAL_WINDOW_SIZE_PACKETS,
                                  set(), list(), 20 * MEGABYTE, 1)
    flows.append(f1)
    h1.flows["F1"] = f1

    # (links, flows, hosts, routers) but we have no routers
    network = NetworkTopology(links, flows, hosts, None)
    network.write_to_json("test_case0_dummy.json")

    # generate for FlowReno
    flows = list()
    f1 = FlowReno("F1", "H1", "H2", h1, h2, INITIAL_WINDOW_SIZE_PACKETS,
                                  set(), list(), 20 * MEGABYTE, 1)
    flows.append(f1)
    h1.flows["F1"] = f1  # overwrites existing FlowDummy in h1
    network = NetworkTopology(links, flows, hosts, None)
    network.write_to_json("test_case0_reno.json")

    # generate for FlowFast
    flows = list()
    f1 = FlowFast("F1", "H1", "H2", h1, h2, INITIAL_WINDOW_SIZE_PACKETS,
                                  set(), list(), 20 * MEGABYTE, 1)
    flows.append(f1)
    h1.flows["F1"] = f1
    network = NetworkTopology(links, flows, hosts, None)
    network.write_to_json("test_case0_fast.json")

    # test case 1
    hosts = list()
    h1 = Host("H1")
    h2 = Host("H2")
    hosts.append(h1)
    hosts.append(h2)

    routers = list()
    r1 = Router("R1")
    r2 = Router("R2")
    r3 = Router("R3")
    r4 = Router("R4")

    links = list()
    l0 = Link("H1", "R1", h1, r1, LinkBuffer(64 * KILOBYTE), 0.01, 12.5 * KILOBYTE, False)
    l1 = Link("R1", "R2", r1, r2, LinkBuffer(64 * KILOBYTE), 0.01, 10 * KILOBYTE, False)
    l2 = Link("R1", "R3", r1, r3, LinkBuffer(64 * KILOBYTE), 0.01, 10 * KILOBYTE, False)
    l3 = Link("R2", "R4", r2, r4, LinkBuffer(64 * KILOBYTE), 0.01, 10 * KILOBYTE, False)
    l4 = Link("R3", "R4", r3, r4, LinkBuffer(64 * KILOBYTE), 0.01, 10 * KILOBYTE, False)
    l5 = Link("R4", "H2", r4, h2, LinkBuffer(64 * KILOBYTE), 0.01, 12.5 * KILOBYTE, False)
    links.append(l0)
    links.append(l1)
    links.append(l2)
    links.append(l3)
    links.append(l4)
    links.append(l5)
    h1.link = l0
    h2.link = l5
    r1.links.append(l0)
    r1.links.append(l1)
    r1.links.append(l2)
    r2.links.append(l1)
    r2.links.append(l3)
    r3.links.append(l2)
    r3.links.append(l4)
    r4.links.append(l3)
    r4.links.append(l4)
    r4.links.append(l5)

    # Dummy
    flows = list()
    f1 = FlowDummy("F1", "H1", "H2", h1, h2, INITIAL_WINDOW_SIZE_PACKETS,
                                  set(), list(), 20 * MEGABYTE, 0.5)
    flows.append(f1)
    h1.flows["F1"] = f1
    network = NetworkTopology(links, flows, hosts, routers)
    network.write_to_json("test_case1_dummy.json")

    # Reno
    flows = list()
    f1 = FlowReno("F1", "H1", "H2", h1, h2, INITIAL_WINDOW_SIZE_PACKETS,
                                  set(), list(), 20 * MEGABYTE, 0.5)
    flows.append(f1)
    h1.flows["F1"] = f1
    network = NetworkTopology(links, flows, hosts, routers)
    network.write_to_json("test_case1_reno.json")

    # FAST
    flows = list()
    f1 = FlowFast("F1", "H1", "H2", h1, h2, INITIAL_WINDOW_SIZE_PACKETS,
                                  set(), list(), 20 * MEGABYTE, 0.5)
    flows.append(f1)
    h1.flows["F1"] = f1
    network = NetworkTopology(links, flows, hosts, routers)
    network.write_to_json("test_case1_fast.json")
