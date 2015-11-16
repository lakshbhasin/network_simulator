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
    l1 = Link(end_1_addr = "H1", end_2_addr = "H2", link_buffer =
            LinkBuffer(max_buffer_size_bits = 64 * KILOBYTE),
            static_delay_sec = 0.01, capacity_bps = 10 * MEGABYTE)
    links.append(l1)

    hosts = list()
    h1 = Host("H1")
    h2 = Host("H2")
    hosts.append(h1)
    hosts.append(h2)

    # generate for FlowDummy
    flows = list()
    f1 = FlowDummy(flow_id = "F1", source_addr = "H1", dest_addr = "H2",
                                  data_size_bits = 20 * MEGABYTE,
                                  start_time_sec = 1)
    flows.append(f1)

    network = NetworkTopology(links = links, flows = flows, hosts = hosts)
    network.write_to_json("data/test_case_0_dummy.json")

    # generate for FlowReno
    flows = list()
    f1 = FlowReno(flow_id = "F1", source_addr = "H1", dest_addr = "H2",
                                  data_size_bits = 20 * MEGABYTE,
                                  start_time_sec = 1)
    flows.append(f1)
    network = NetworkTopology(links = links, flows = flows, hosts = hosts)
    network.write_to_json("data/test_case_0_reno.json")

    # generate for FlowFast
    flows = list()
    f1 = FlowFast(flow_id = "F1", source_addr = "H1", dest_addr = "H2",
                                  data_size_bits = 20 * MEGABYTE,
                                  start_time_sec = 1)
    flows.append(f1)
    network = NetworkTopology(links = links, flows = flows, hosts = hosts)
    network.write_to_json("data/test_case_0_fast.json")

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
    l0 = Link(end_1_addr = "H1", end_2_addr = "R1", link_buffer =
            LinkBuffer(max_buffer_size_bits = 64 * KILOBYTE),
            static_delay_sec = 0.01, capacity_bps = 12.5 * MEGABYTE)
    l1 = Link(end_1_addr = "R1", end_2_addr = "R2", link_buffer =
            LinkBuffer(max_buffer_size_bits = 64 * KILOBYTE),
            static_delay_sec = 0.01, capacity_bps = 10 * MEGABYTE)
    l2 = Link(end_1_addr = "R1", end_2_addr = "R3", link_buffer =
            LinkBuffer(max_buffer_size_bits = 64 * KILOBYTE),
            static_delay_sec = 0.01, capacity_bps = 10 * MEGABYTE)
    l3 = Link(end_1_addr = "R2", end_2_addr = "R4", link_buffer =
            LinkBuffer(max_buffer_size_bits = 64 * KILOBYTE),
            static_delay_sec = 0.01, capacity_bps = 10 * MEGABYTE)
    l4 = Link(end_1_addr = "R3", end_2_addr = "R4", link_buffer =
            LinkBuffer(max_buffer_size_bits = 64 * KILOBYTE),
            static_delay_sec = 0.01, capacity_bps = 10 * MEGABYTE)
    l5 = Link(end_1_addr = "R4", end_2_addr = "H2", link_buffer =
            LinkBuffer(max_buffer_size_bits = 64 * KILOBYTE),
            static_delay_sec = 0.01, capacity_bps = 12.5 * MEGABYTE)
    links.append(l0)
    links.append(l1)
    links.append(l2)
    links.append(l3)
    links.append(l4)
    links.append(l5)

    # Dummy
    flows = list()
    f1 = FlowDummy(flow_id = "F1", source_addr = "H1", dest_addr = "H2",
                                  data_size_bits = 20 * MEGABYTE,
                                  start_time_sec = 0.5)
    flows.append(f1)
    network = NetworkTopology(links = links, flows = flows, hosts = hosts, 
            routers = routers)
    network.write_to_json("data/test_case_1_dummy.json")

    # Reno
    flows = list()
    f1 = FlowReno(flow_id = "F1", source_addr = "H1", dest_addr = "H2",
                                  data_size_bits = 20 * MEGABYTE,
                                  start_time_sec = 0.5)
    flows.append(f1)
    network = NetworkTopology(links = links, flows = flows, hosts = hosts, 
            routers = routers)
    network.write_to_json("data/test_case_1_reno.json")

    # FAST
    flows = list()
    f1 = FlowFast(flow_id = "F1", source_addr = "H1", dest_addr = "H2",
                                  data_size_bits = 20 * MEGABYTE,
                                  start_time_sec = 0.5)
    flows.append(f1)
    network = NetworkTopology(links = links, flows = flows, hosts = hosts, 
            routers = routers)
    network.write_to_json("data/test_case_1_fast.json")
