"""
Main entry-point into the network simulation. Run this script with the -h
flag to see usage.

Example usage (from root directory of project):
    python initializer.py -v INFO -f log/log.txt data/test_case_0.json

This will take data/test_case_0.json as the input NetworkTopology. The log
level will be set to "INFO", with the file log/log.txt used as the log file.
In order to log to stdout, just leave out the optional -f parameter.
"""

import argparse
import logging
import sys

from network_simulator.main_event_loop import MainEventLoop
from network_simulator.network_topology import NetworkTopology
from network_simulator.flow import *
from network_simulator.router import *

if __name__ == "__main__":
    log_choices = ["DEBUG", "INFO", "WARNING"]
    logging_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    parser = argparse.ArgumentParser(
        description='Run the network simulator.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-v", "--verbosity", type=str, default="WARNING",
                        help="Log verbosity. Choices are: " +
                             ", ".join(log_choices),
                        choices=log_choices,
                        metavar='')
    parser.add_argument("-f", "--log_file", type=str, default="stdout",
                        help="Log file",
                        metavar='')
    parser.add_argument("topology_json", type=str,
                        help="JSON file containing the NetworkTopology")
    args = parser.parse_args()

    # Based on the chosen verbosity, set the log level.
    log_level_str = args.verbosity.upper()
    log_level = getattr(logging, log_level_str)

    # Default the log output to stdout if not given, and finish log setup for
    # use throughout the rest of the modules.
    log_file = args.log_file
    if log_file == "stdout":
        logging.basicConfig(stream=sys.stdout, level=log_level,
                            format=logging_format)
    else:
        logging.basicConfig(filename=log_file, filemode='w', level=log_level,
                            format=logging_format)

    # Check the topology file is a JSON one.
    topology_json = args.topology_json
    if not topology_json.lower().endswith(".json"):
        parser.error("topology_json file must end with '.json'")

    logger = logging.getLogger(__name__)
    logger.info("Log level set to: %s", log_level_str)
    logger.info("Logging to: %s", log_file)
    logger.info("Topology file: %s", topology_json)

    # Set up NetworkTopology
    topology = NetworkTopology.init_from_json_file(topology_json)

    # Set up event loop and statistics, and register initial Events
    event_loop = MainEventLoop()

    # if routers not None, schedule events immediately
    if topology.routers is not None:
        for router in topology.routers:
            event_loop.schedule_event_with_delay(InitiateRoutingTableUpdateEvent(router),0)

    # flows is never None right?...
    for flow in topology.flows:
        event_loop.schedule_event_with_delay(InitiateFlowEvent(flow), 
                                             flow.start_time_sec)

    event_loop.run()
