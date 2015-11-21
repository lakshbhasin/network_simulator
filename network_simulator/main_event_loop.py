"""
Module for the MainEventLoop class.
"""

from Queue import PriorityQueue
import logging

from statistics import Statistics
from flow import InitiateFlowEvent, FlowCompleteEvent

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

        # Count the number of InitiateFlowEvents to track how many Flows need
        # to complete before we exit.
        num_flows_left = 0
        for _, this_event in self.events.queue:
            if isinstance(this_event, InitiateFlowEvent):
                num_flows_left += 1

        if num_flows_left == 0:
            raise ValueError("No Flows were scheduled to run.")

        # Keep picking next Event by time from the PriorityQueue, run it,
        # and schedule new Events, until either the Event queue is empty or
        # the total number of flows has been reached.
        while not self.events.empty() and num_flows_left > 0:
            next_event_start_time, next_event = self.events.get_nowait()

            # Ensure not travelling backwards in time.
            if next_event_start_time < self.global_clock_sec:
                raise ValueError("Next event starts at "
                                 + next_event_start_time + " s, which is "
                                 + "before " + self.global_clock_sec + " s.")

            self.global_clock_sec = next_event_start_time

            try:
                next_event.run(self, self.statistics)
                next_event.schedule_new_events(self)
            except:
                # TODO(team): Output Statistics collected so far.
                logger.warning("Unexpected error. Outputting Statistics...")
                raise

            if isinstance(next_event, FlowCompleteEvent):
                num_flows_left -= 1

        logger.info("Finished running main Event loop.")

        # TODO(team): Output final Statistics
