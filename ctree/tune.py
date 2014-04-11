import logging
log = logging.getLogger(__name__)

import abc
import itertools

class TuningDriver(object):
    """
    Object that interacts with backend tuners. Provides
    an infinite stream of configurations, as well as an
    interface to report on the performance of each.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        """
        Creates a tuner to search in the given space.
        """
        self.configs = self._get_configs()

    @abc.abstractmethod
    def _get_configs(self):
        """A generator that yields a stream of configurations."""
        pass

    @abc.abstractmethod
    def report(self, **kwargs):
        """Reports performance of most recent configuration."""
        pass


class NullTuningDriver(TuningDriver):
    """
    Provides a stream of None's, and ignores reports()s.
    """
    def __init__(self):
        """Do nothing."""
        super(NullTuningDriver, self).__init__()

    def _get_configs(self):
        """Yield the empty configuration."""
        while True:
            yield {}

    def report(self, *args, **kwargs):
        """Ignore reports."""
        pass



class Parameter(object):
    """A dimension of the search space."""
    def __init__(self, name):
        """Create a parameter with the given name."""
        self.name = name


class IntegerParameter(Parameter):
    """An integer parameter."""
    def __init__(self, name, lower_bound, upper_bound):
        """Create an int parameter with value in range(lb, ub)."""
        super(IntegerParameter, self).__init__(name)
        self._values = range(lower_bound, upper_bound)

    def values(self):
        return self._values


class BooleanParameter(Parameter):
    """A boolean parameter."""
    def __init__(self, name):
        """Create a bool parameter."""
        super(BooleanParameter, self).__init__(name)
        self._values = [True, False]

    def values(self):
        return self._values


class EnumParameter(Parameter):
    """A enum parameter."""
    def __init__(self, name, values):
        """Create an enum parameter."""
        super(EnumParameter, self).__init__(name)
        self._values = values

    def values(self):
        return self._values


class Result(object):
    """
    Captures the performance of a tuning run.
    """
    def __init__(self, time       = float('inf'),
                       accuracy   = float('-inf'),
                       energy     = float('inf'),
                       size       = float('inf'),
                       confidence = float('-inf')):
        self.time = time
        self.accuracy = accuracy
        self.energy = energy
        self.size = size
        self.confidence = confidence


class Objective(object):
    def compare(self, result0, result1):
        raise NotImplementedException()


class MinimizeTime(Objective):
    def compare(self, result0, result1):
        return result0.time < result1.time


class BruteForceTuningDriver(TuningDriver):
    """
    Yields all points in the hyperrectangular space defined by
    the cartesian product of all input parameters. Then, yields
    the best point for the rest of time.
    """
    def __init__(self, params, objective):
        """Initialize with the given objective."""
        super(BruteForceTuningDriver, self).__init__()
        self._objective = objective
        self._best_result = Result()
        self._best_cfg = None
        self._last_cfg = None
        self._params = params

    def _get_configs(self):
        """A generator of all configurations."""
        # compute the cartesian product of the dimensions
        names, values = zip(*[(p.name, p.values()) for p in self._params])
        for cfg_values in itertools.product(*values):
            cfg = {k: v for k,v in zip(names, cfg_values)}
            self._last_cfg = cfg
            yield cfg

        assert self._best_cfg != None, \
            "No best configuration. Did you call report()?"

        # return the best for the rest of time
        while True:
            yield self._best_cfg

    def report(self, **kwargs):
        """
        Record the new result if it is better than the current best.
        """
        new_result = Result(**kwargs)
        if self._objective.compare(new_result, self._best_result):
            self._best_result = new_result
            self._best_cfg = self._last_cfg
