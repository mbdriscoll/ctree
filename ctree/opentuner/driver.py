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


class OpenTunerDriver(TuningDriver):
    """
    Object that interacts with backend tuners. Provides
    a stream of configurations, as well as an interface
    to report on the performance of each.
    """
    def __init__(self, manipulator, opentuner_args=None):
        """
        Creates communication queues and spawn a thread
        to run the tuning logic.
        """
        assert isinstance(manipulator, ConfigurationManipulator)
        self._results = queue.Queue(1)
        self._configs = queue.Queue(1)
        ot_args = opentuner_args if opentuner_args else []
        self._thread = OpenTunerThread(manipulator, self._results, self._configs, ot_args)
        self._thread.start()

    def get_next_config(self):
        """Get the next configuration to test."""
        timeout = CONFIG.getint("opentuner", "timeout")
        try:
            return self._configs.get(True, timeout)
        except queue.Empty:
            log.warning("exhausted stream of tuning configurations")
        return None

    def report(self, **kwargs):
        """Report the performance of the most recent configuration."""
        timeout = CONFIG.getint("opentuner", "timeout")
        result = Result(**kwargs)
        try:
            self._results.put(result, True, timeout)
        except queue.Full:
            log.warning("exhausted stream of tuning configurations")


class OpenTunerThread(threading.Thread):
    """
    Thread to drive OpenTuner.
    """
    def __init__(self, manipulator, results_queue, configs_queue, opentuner_args=None):
        super(OpenTunerThread, self).__init__()
        self._manipulator = manipulator
        self._results = results_queue
        self._configs = configs_queue
        self._opentuner_args = opentuner_args if opentuner_args else []
        assert isinstance(opentuner_args, list), \
            "Expected a list of OpenTuner args, but got an '%s'." % \
            type(opentuner_args)
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
        tuner_args = arg_parser.parse_args(config_args + self._opentuner_args)
        interface = CtreeMeasurementInterface(self._manipulator, self._results, self._configs)
        TuningRunMain(interface, tuner_args).main()
        log.info("tuning thread '%s' terminating.", self.name)


class CtreeMeasurementInterface(MeasurementInterface):
    """
    Ctree interface to opentuner.
    """
    def __init__(self, manipulator, results_queue, configs_queue, *args, **kwargs):
        """
        Create a new measurement interface with knowledge of the
        queues to communicate with the ctree jit module.
        """
        super(CtreeMeasurementInterface, self).__init__(*args, **kwargs)
        self._manipulator = manipulator
        self._results = results_queue
        self._configs = configs_queue

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
        timeout = CONFIG.getint("opentuner", "timeout")
        self._configs.put(desired_result.configuration, True, timeout)
        return self._results.get(True, timeout)

    def save_final_config(self, configuration):
        """Report best configuration."""
        log.info("best configuration found to be: %s", configuration)
