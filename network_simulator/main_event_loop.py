"""
Module for the MainEventLoop class.
"""

from Queue import PriorityQueue
import logging

from .statistics import *

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
        :return:
        """
        self.global_clock_sec = 0.0
        self.events = PriorityQueue()
        self.statistics = Statistics()

    def schedule_event_with_delay(self, event, delay_sec):
        """
        Schedules an event delay_sec from now.
        :param float delay_sec: non-negative time delay.
        :return:
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

        # Keep picking next Event by time from the PriorityQueue, run it,
        # and schedule new Events.
        while not self.events.empty():
            next_event_start_time, next_event = self.events.get_nowait()

            # Ensure not travelling backwards in time.
            assert next_event_start_time >= self.global_clock_sec
            self.global_clock_sec = next_event_start_time

            next_event.run(self.statistics)
            next_event.schedule_new_events(self)

            # TODO(laksh): If all of the remaining Events are just periodic
            # Events like InitiateRoutingTableUpdateEvent, we need to exit
            # this loop since the network sim is basically done. Maybe hold a
            # global state variable for the event loop saying it's done
            # processing all the flows or something, and have a
            # FlowCompleteEvent.

        logging.info("Finished running main Event loop.")
