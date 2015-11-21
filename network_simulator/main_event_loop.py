"""
Module for the MainEventLoop class.
"""

from Queue import PriorityQueue
import logging

from statistics import Statistics
from flow import FlowCompleteEvent, InitiateFlowEvent, PeriodicFlowInterrupt

logger = logging.getLogger(__name__)


class MainEventLoop(object):
    """
    An event loop that holds all of the events that are going to occur,
    and also keeps track of Statistics for the network.
    """

    def __init__(self):
        """
        :ivar float global_clock_sec: global clock that advances on
        completion of Events.
        :ivar PriorityQueue events: a priority queue of (start_time_sec,
        Event) tuples, used to easily retrieve the (earliest) next Event.
        :ivar Statistics statistics: statistics for this network.
        """
        self.global_clock_sec = 0.0
        self.events = PriorityQueue()
        self.statistics = Statistics()

    def schedule_event_with_delay(self, event, delay_sec):
        """
        Schedules an event delay_sec from now.
        :param float delay_sec: non-negative time delay.
        """
        if delay_sec < 0.0:
            raise ValueError("Tried to schedule an Event with negative delay.")

        event_start_time = self.global_clock_sec + delay_sec
        self.events.put_nowait((event_start_time, event))

    def run(self):
        """
        Entry point into running this event loop. There should be some Events
        in the queue at this point.
        """
        if self.events.empty():
            raise ValueError("Tried to run an empty event loop.")

        # Track the IDs of Flows that are not yet complete.
        incomplete_flow_ids = list()
        for _, this_event in self.events.queue:
            if isinstance(this_event, InitiateFlowEvent):
                incomplete_flow_ids.append(this_event.flow.flow_id)

        if len(incomplete_flow_ids) == 0:
            raise ValueError("No Flows were scheduled to run.")

        # Variables for printing periodic updates in Event loop
        prev_print_clock_sec = 0.0
        print_threshold_sec = 0.5

        # Keep picking next Event by time from the PriorityQueue, run it,
        # and schedule new Events, until the total number of flows has been
        # reached.
        while len(incomplete_flow_ids) > 0:
            next_event_start_time, next_event = self.events.get_nowait()

            # Ensure not travelling backwards in time.
            if next_event_start_time < self.global_clock_sec:
                raise ValueError("Next event starts at "
                                 + next_event_start_time + " s, which is "
                                 + "before " + self.global_clock_sec + " s.")

            self.global_clock_sec = next_event_start_time

            # Do not handle periodic interrupts for Flows that are done.
            if isinstance(next_event, PeriodicFlowInterrupt) \
                    and next_event.flow.flow_id not in incomplete_flow_ids:
                logger.info("Stopped handling PeriodicFlowInterrupts for "
                            "completed Flow %s", next_event.flow.flow_id)
            else:
                # Run Event and schedule new Events as usual.
                try:
                    next_event.run(self, self.statistics)
                    next_event.schedule_new_events(self)
                except:
                    # TODO(team): Output Statistics collected so far.
                    logger.warning("Unexpected error. Outputting Statistics...")
                    raise

            if isinstance(next_event, FlowCompleteEvent):
                incomplete_flow_ids.remove(next_event.flow.flow_id)

            if self.global_clock_sec - prev_print_clock_sec > \
                    print_threshold_sec:
                logger.info("Finished processing Events through %f sec",
                            self.global_clock_sec)
                prev_print_clock_sec = self.global_clock_sec

        logger.info("Finished running main Event loop.")
        logger.info("Time taken: %f s.", self.global_clock_sec)

        # TODO(team): Output final Statistics
