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
        self._thread = OpenTunerThread(self, *ot_args, **ot_kwargs)
        self._best = None
        self._thread.start()

    def _get_configs(self):
        """Get the next configuration to test."""
        timeout = CONFIG.getint("opentuner", "timeout")
        while self._best == None:
            try:
                yield self._configs.get(True, timeout)
            except queue.Empty:
                log.warning("exhausted stream of tuning configurations")
                break
        while True:
            yield self._best

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
    def __init__(self, driver, *ot_args, **ot_kwargs):
        super(OpenTunerThread, self).__init__()
        self._driver = driver
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
        interface = CtreeMeasurementInterface(self._driver, *self._ot_args, **self._ot_kwargs)
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
        self._results = driver._results
        self._configs = driver._configs

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
        driver.best = configuration
