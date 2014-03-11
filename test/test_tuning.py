import unittest

import os
import shutil
import itertools

class TestNullTuningDriver(unittest.TestCase):
    def test_import(self):
        import ctree.tune

    def test_null_driver_stream(self):
        from ctree.tune import NullTuningDriver

        driver = NullTuningDriver()
        for i in range(4):
            self.assertIsNone(driver.get_configs().next())

    def test_null_driver_report(self):
        from ctree.tune import NullTuningDriver

        driver = NullTuningDriver()
        for i in range(4):
            config = driver.get_configs().next()
            driver.report(time=0.4)


try:
    import opentuner
except ImportError:
    HAVE_OPENTUNER = False
else:
    HAVE_OPENTUNER = True


class TestOpenTunerDriver(unittest.TestCase):
    @unittest.skipUnless(HAVE_OPENTUNER, "OpenTuner not in PYTHONPATH.")
    def test_import(self):
        from ctree.opentuner.driver import OpenTunerDriver

    @unittest.skipUnless(HAVE_OPENTUNER, "OpenTuner not in PYTHONPATH.")
    def test_1d_config(self):
        from ctree.opentuner.driver import OpenTunerDriver
        from opentuner.search.objective import MinimizeTime
        from opentuner.search.manipulator import (
            ConfigurationManipulator,
            IntegerParameter,
        )

        cfg = ConfigurationManipulator()
        cfg.add_parameter( IntegerParameter("foo", 0, 199) )
        driver = OpenTunerDriver(manipulator=cfg, objective=MinimizeTime())

        unsearched = set(range(200))
        for i in range(20):
            cfg = driver.get_configs().next()
            val = cfg.data["foo"]
            driver.report(time=val)
            unsearched.remove(val)
        self.assertEqual(len(unsearched), 180)

    # keep it to one test now because we're having problems
    # with multiple threads and the opentuner sqlite database.


class TestBruteForceTuningDriver(unittest.TestCase):
    def test_import(self):
        from ctree.tune import BruteForceTuningDriver

    def test_bruteforce_driver_1d(self):
        from ctree.tune import (
            BruteForceTuningDriver,
            IntegerParameter,
            MinimizeTime,
            Result,
        )

        objective = MinimizeTime()
        params = [IntegerParameter("foo", 0, 100)]
        driver = BruteForceTuningDriver(params, objective)

        unsearched = set(range(0, 100))
        for config in itertools.islice(driver.get_configs(), 100):
            unsearched.remove(config["foo"])
            driver.report( Result(time=0.4) )
        self.assertSetEqual(unsearched, set())

    def test_bruteforce_driver_2d(self):
        from ctree.tune import (
            BruteForceTuningDriver,
            IntegerParameter,
            MinimizeTime,
            Result,
        )

        params = [
            IntegerParameter("foo", 0, 10),
            IntegerParameter("bar", 0, 10),
        ]
        driver = BruteForceTuningDriver(params, MinimizeTime())

        unsearched = set(range(0, 100))
        for config in itertools.islice(driver.get_configs(), 100):
            entry = config["foo"] * 10 + config["bar"]
            unsearched.remove(entry)
            driver.report( Result(time=0.4) )
        self.assertSetEqual(unsearched, set())
