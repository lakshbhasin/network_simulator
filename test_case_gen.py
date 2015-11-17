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

    # test case 2
    hosts = list()
    s1 = Host("S1")
    s2 = Host("S2")
    s3 = Host("S3")
    t1 = Host("T1")
    t2 = Host("T2")
    t3 = Host("T3")
    hosts.append(s1)
    hosts.append(s2)
    hosts.append(s3)
    hosts.append(t1)
    hosts.append(t2)
    hosts.append(t3)

    routers = list()
    r1 = Router("R1")
    r2 = Router("R2")
    r3 = Router("R3")
    r4 = Router("R4")

    # router-router
    links = list()
    l1 = Link(end_1_addr = "R1", end_2_addr = "R2", link_buffer =
            LinkBuffer(max_buffer_size_bits = 128 * KILOBYTE),
            static_delay_sec = 0.01, capacity_bps = 10 * MEGABYTE)
    l2 = Link(end_1_addr = "R2", end_2_addr = "R3", link_buffer =
            LinkBuffer(max_buffer_size_bits = 128 * KILOBYTE),
            static_delay_sec = 0.01, capacity_bps = 10 * MEGABYTE)
    l3 = Link(end_1_addr = "R3", end_2_addr = "R4", link_buffer =
            LinkBuffer(max_buffer_size_bits = 128 * KILOBYTE),
            static_delay_sec = 0.01, capacity_bps = 10 * MEGABYTE)
    links.append(l1)
    links.append(l2)
    links.append(l3)
    lh1 = Link(end_1_addr = "S1", end_2_addr = "R1", link_buffer =
            LinkBuffer(max_buffer_size_bits = 128 * KILOBYTE),
            static_delay_sec = 0.01, capacity_bps = 12.5 * MEGABYTE)
    lh2 = Link(end_1_addr = "T1", end_2_addr = "R4", link_buffer =
            LinkBuffer(max_buffer_size_bits = 128 * KILOBYTE),
            static_delay_sec = 0.01, capacity_bps = 12.5 * MEGABYTE)
    lh3 = Link(end_1_addr = "S2", end_2_addr = "R1", link_buffer =
            LinkBuffer(max_buffer_size_bits = 128 * KILOBYTE),
            static_delay_sec = 0.01, capacity_bps = 12.5 * MEGABYTE)
    lh4 = Link(end_1_addr = "T2", end_2_addr = "R2", link_buffer =
            LinkBuffer(max_buffer_size_bits = 128 * KILOBYTE),
            static_delay_sec = 0.01, capacity_bps = 12.5 * MEGABYTE)
    lh5 = Link(end_1_addr = "S3", end_2_addr = "R3", link_buffer =
            LinkBuffer(max_buffer_size_bits = 128 * KILOBYTE),
            static_delay_sec = 0.01, capacity_bps = 12.5 * MEGABYTE)
    lh6 = Link(end_1_addr = "T3", end_2_addr = "R4", link_buffer =
            LinkBuffer(max_buffer_size_bits = 128 * KILOBYTE),
            static_delay_sec = 0.01, capacity_bps = 12.5 * MEGABYTE)
    links.append(lh1)
    links.append(lh2)
    links.append(lh3)
    links.append(lh4)
    links.append(lh5)
    links.append(lh6)

    # Dummy
    flows = list()
    f1 = FlowDummy(flow_id = "F1", source_addr = "S1", dest_addr = "T1",
                                  data_size_bits = 35 * MEGABYTE,
                                  start_time_sec = 0.5)
    f2 = FlowDummy(flow_id = "F2", source_addr = "S2", dest_addr = "T2",
                                  data_size_bits = 15 * MEGABYTE,
                                  start_time_sec = 10)
    f3 = FlowDummy(flow_id = "F3", source_addr = "S3", dest_addr = "T3",
                                  data_size_bits = 30 * MEGABYTE,
                                  start_time_sec = 20)
    flows.append(f1)
    flows.append(f2)
    flows.append(f3)
    network = NetworkTopology(links = links, flows = flows, hosts = hosts, 
            routers = routers)
    network.write_to_json("data/test_case_2_dummy.json")

    # Reno
    flows = list()
    f1 = FlowReno(flow_id = "F1", source_addr = "S1", dest_addr = "T1",
                                  data_size_bits = 35 * MEGABYTE,
                                  start_time_sec = 0.5)
    f2 = FlowReno(flow_id = "F2", source_addr = "S2", dest_addr = "T2",
                                  data_size_bits = 15 * MEGABYTE,
                                  start_time_sec = 10)
    f3 = FlowReno(flow_id = "F3", source_addr = "S3", dest_addr = "T3",
                                  data_size_bits = 30 * MEGABYTE,
                                  start_time_sec = 20)
    flows.append(f1)
    flows.append(f2)
    flows.append(f3)
    network = NetworkTopology(links = links, flows = flows, hosts = hosts, 
            routers = routers)
    network.write_to_json("data/test_case_2_reno.json")

    # FAST
    flows = list()
    f1 = FlowFast(flow_id = "F1", source_addr = "S1", dest_addr = "T1",
                                  data_size_bits = 35 * MEGABYTE,
                                  start_time_sec = 0.5)
    f2 = FlowFast(flow_id = "F2", source_addr = "S2", dest_addr = "T2",
                                  data_size_bits = 15 * MEGABYTE,
                                  start_time_sec = 10)
    f3 = FlowFast(flow_id = "F3", source_addr = "S3", dest_addr = "T3",
                                  data_size_bits = 30 * MEGABYTE,
                                  start_time_sec = 20)
    flows.append(f1)
    flows.append(f2)
    flows.append(f3)
    network = NetworkTopology(links = links, flows = flows, hosts = hosts, 
            routers = routers)
    network.write_to_json("data/test_case_2_fast.json")
