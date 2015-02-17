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
from opentuner.api import TuningRunManager


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
        self._best_config = None
        interface = CtreeMeasurementInterface(self, *ot_args, **ot_kwargs)
        arg_parser = argparse.ArgumentParser(parents=opentuner.argparsers())
        config_args = CONFIG.get("opentuner", "args").split()
        tuner_args = arg_parser.parse_args(config_args)
        self.manager = TuningRunManager(interface, tuner_args)
        self._converged = False

    def _get_configs(self):
        """Get the next configuration to test."""
        timeout = CONFIG.getint("opentuner", "timeout")
        while True:
            self.curr_desired_result = self.manager.get_next_desired_result()
            if self.curr_desired_result is None:
                break
            yield self.curr_desired_result.configuration.data
            print("Best configuration", self.manager.get_best_configuration())

        log.info("exhausted stream of configurations.")
        best_config = self.manager.get_best_configuration()
        assert best_config != None, "No best configuration reported."
        self._converged = True
        while True:
            yield best_config

    def report(self, **kwargs):
        """Report the performance of the most recent configuration."""
        if not self._converged:
            print("Tuning run result:", self.curr_desired_result.configuration.data, kwargs)
            self.manager.report_result(self.curr_desired_result, Result(**kwargs))
            # result = Result(**kwargs)
            # self._results.put_nowait(result)


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
