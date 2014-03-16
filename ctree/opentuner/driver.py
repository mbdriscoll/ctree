import logging
log = logging.getLogger(__name__)

import threading
import argparse
import Queue as queue # queue in 3.x

from ctree import CONFIG
from ctree.tune import TuningDriver

import opentuner
from opentuner.measurement import MeasurementInterface
from opentuner.resultsdb.models import Result
from opentuner.tuningrunmain import TuningRunMain
from opentuner.search.manipulator import ConfigurationManipulator
from opentuner.measurement.inputmanager import FixedInputManager


class OpenTunerDriver(TuningDriver):
    """
    Object that interacts with backend tuners. Provides
    a stream of configurations, as well as an interface
    to report on the performance of each.
    """
    def __init__(self, *ot_args, **ot_kwargs):
        """
        Creates communication queues and spawn a thread
        to run the tuning logic.
        """
        super(OpenTunerDriver, self).__init__()
        self._results = queue.Queue(1)
        self._configs = queue.Queue(1)
        self._best_config = None
        self._thread = OpenTunerThread(self, *ot_args, **ot_kwargs)
        self._thread.start()
        self._converged = False

    def _get_configs(self):
        """Get the next configuration to test."""
        timeout = CONFIG.getint("opentuner", "timeout")
        while True:
            try:
                yield self._configs.get(True, timeout)
            except queue.Empty:
                break

        log.info("exhausted stream of configurations.")
        assert self._best_config != None, "No best configuration reported."
        self._converged = True
        while True:
            yield self._best_config

    def report(self, **kwargs):
        """Report the performance of the most recent configuration."""
        if not self._converged:
            result = Result(**kwargs)
            self._results.put_nowait(result)


class OpenTunerThread(threading.Thread):
    """
    Thread to drive OpenTuner.
    """
    def __init__(self, driver, *ot_args, **ot_kwargs):
        super(OpenTunerThread, self).__init__()
        self._ctree_driver = driver
        self._ot_args = ot_args
        self._ot_kwargs = ot_kwargs
        self._tuningrun = None

        # variables for Thread class
        self.name = "opentuner_driver"
        self.daemon = True

    def run(self):
        """Starts the main OpenTuner loop."""
        log.info("tuning thread '%s' starting (%d total threads now).", \
            self.name, threading.active_count())
        arg_parser = argparse.ArgumentParser(parents=opentuner.argparsers())
        config_args = CONFIG.get("opentuner", "args").split()
        tuner_args = arg_parser.parse_args(config_args)
        interface = CtreeMeasurementInterface(self._ctree_driver, *self._ot_args, **self._ot_kwargs)
        TuningRunMain(interface, tuner_args).main()
        log.info("tuning thread '%s' terminating.", self.name)


class CtreeMeasurementInterface(MeasurementInterface):
    """
    Ctree interface to opentuner.
    """
    def __init__(self, driver, *args, **kwargs):
        """
        Create a new measurement interface with knowledge of the
        queues to communicate with the ctree jit module.
        """
        kwargs['input_manager'] = FixedInputManager()
        super(CtreeMeasurementInterface, self).__init__(*args, **kwargs)
        self._ctree_driver = driver

    def manipulator(self):
        """
        Retrieves the tuning space originally provided
        by the specializer.
        """
        return self._manipulator

    def run(self, desired_result, input, limit):
        """
        Build the program specified by 'desired_result' and report
        its performance. With threading, we place the config in the
        output queue, then wait for a Result in the input queue.
        """
        self._ctree_driver._configs.put(desired_result.configuration.data, True)
        return self._ctree_driver._results.get(True)

    def save_final_config(self, configuration):
        """Report best configuration."""
        log.info("best configuration found to be: %s", configuration)
        self._ctree_driver._best_config = configuration.data
