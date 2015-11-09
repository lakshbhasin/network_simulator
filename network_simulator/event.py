"""
Module for the abstract Event class. Subclasses containing more specific
information about the event that occurred are in different classes (e.g.
Router-related events are in router.py).
"""

from abc import ABCMeta, abstractmethod


class Event(object):
    """
    Representation of a general (abstract) Event.
    """
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def run(self, main_event_loop, statistics):
        """
        Carries out the actions of this Event and updates statistics.
        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        :param Statistics statistics: the Statistics to update
        """
        pass

    @abstractmethod
    def schedule_new_events(self, main_event_loop):
        """
        Schedules new Events. This is called immediately after run().
        :param MainEventLoop main_event_loop: event loop where new Events will
        be scheduled.
        """
        pass
