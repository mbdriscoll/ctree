import logging
log = logging.getLogger(__name__)

import abc

class Tuner(object):
    """
    Object that interacts with backend tuners. Provides
    an infinite stream of configurations, as well as an
    interface to report on the performance of each.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, manipulator):
        """
        Creates a tuner to search in the given space.
        """
        pass

    @abc.abstractmethod
    def get_next_config(self):
        """Get the next configuration to test."""
        pass

    @abc.abstractmethod
    def report(self, time=float('inf'), accuracy=None, energy=None, size=None, confidence=None):
        """Reports performance of most recent configuration."""
        pass


class NullTuningDriver(object):
    """
    Provides a stream of None's, and ignores reports()s.
    """
    def __init__(self):
        """Do nothing."""
        pass

    def get_next_config(self):
        """Yield the empty configuration."""
        return None

    def report(self, *args, **kwargs):
        """Ignore reports."""
        pass
