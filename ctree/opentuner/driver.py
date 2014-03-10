import logging
log = logging.getLogger(__name__)

import threading
import argparse
import Queue as queue # queue in 3.x

import ctree
from ctree.tune import TuningDriver

import opentuner
from opentuner.measurement import MeasurementInterface
from opentuner.resultsdb.models import Result
from opentuner.tuningrunmain import TuningRunMain
import opentuner.search.manipulator as ot

# copy relevant names into ctree.tune namespace
ConfigurationManipulator = ot.ConfigurationManipulator
Parameter              = ot.Parameter
PrimitiveParameter     = ot.PrimitiveParameter
NumericParameter       = ot.NumericParameter
IntegerParameter       = ot.IntegerParameter
FloatParameter         = ot.FloatParameter
ScaledNumericParameter = ot.ScaledNumericParameter
LogIntegerParameter    = ot.LogIntegerParameter
LogFloatParameter      = ot.LogFloatParameter
PowerOfTwoParameter    = ot.PowerOfTwoParameter
ComplexParameter       = ot.ComplexParameter
BooleanParameter       = ot.BooleanParameter
SwitchParameter        = ot.SwitchParameter
EnumParameter          = ot.EnumParameter
PermutationParameter   = ot.PermutationParameter
ScheduleParameter      = ot.ScheduleParameter
SelectorParameter      = ot.SelectorParameter
ArrayParameter         = ot.ArrayParameter
BooleanArrayParameter  = ot.BooleanArrayParameter
ParameterProxy         = ot.ParameterProxy

class OpenTunerThread(threading.Thread):
    """
    Thread to drive OpenTuner.
    """
    def __init__(self, manipulator, results_queue, configs_queue):
        super(OpenTunerThread, self).__init__()
        self._manipulator = manipulator
        self._results = results_queue
        self._configs = configs_queue
        self.daemon = True

    def run(self):
        """Starts the main OpenTuner loop."""
        from ctree import CONFIG

        log.info("tuning thread '%s' starting.", self.name)
        arg_parser = argparse.ArgumentParser(parents=opentuner.argparsers())
        tuner_args = arg_parser.parse_args(CONFIG.get("tuning", "opentuner_args").split())
        interface = CtreeMeasurementInterface(self._manipulator, self._results, self._configs)
        TuningRunMain(interface, tuner_args).main()
        log.info("tuning thread '%s' terminating.", self.name)


class OpenTunerDriver(TuningDriver):
    """
    Object that interacts with backend tuners. Provides
    a stream of configurations, as well as an interface
    to report on the performance of each.
    """
    def __init__(self, manipulator):
        """
        Creates communication queues and spawn a thread
        to run the tuning logic.
        """
        self._results = queue.Queue(1)
        self._configs = queue.Queue(1)
        OpenTunerThread(manipulator, self._results, self._configs).start()

    def get_next_config(self):
        """Get the next configuration to test."""
        from ctree import CONFIG

        timeout = CONFIG.getint("tuning", "timeout")
        try:
            return self._configs.get(True, timeout)
        except queue.Empty:
            log.warning("exhausted stream of tuning configurations")
        return None

    def report(self, time=float('inf'), accuracy=None, energy=None, size=None, confidence=None):
        """Report the performance of the most recent configuration."""
        from ctree import CONFIG

        timeout = CONFIG.getint("tuning", "timeout")
        result = Result(time=time, accuracy=accuracy, energy=energy, size=size, confidence=confidence)
        try:
            self._results.put(result, True, timeout)
        except queue.Full:
            log.warning("exhausted stream of tuning configurations")


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
        from ctree import CONFIG

        timeout = CONFIG.getint("tuning", "timeout")
        self._configs.put(desired_result.configuration, True, timeout)
        return self._results.get(True, timeout)

    def save_final_config(self, configuration):
        """Report best configuration."""
        log.info("best configuration found to be: %s", configuration)
