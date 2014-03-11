import unittest

import os
import shutil

class TestNullTuningDriver(unittest.TestCase):
    def test_import(self):
        import ctree.tune

    def test_null_driver_stream(self):
        from ctree.tune import NullTuningDriver

        driver = NullTuningDriver()
        for i in range(4):
            self.assertIsNone(driver.get_next_config())

    def test_null_driver_report(self):
        from ctree.tune import NullTuningDriver

        driver = NullTuningDriver()
        for i in range(4):
            config = driver.get_next_config()
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
        from opentuner.search.manipulator import (
            ConfigurationManipulator,
            IntegerParameter,
        )

        cfg = ConfigurationManipulator()
        cfg.add_parameter( IntegerParameter("foo", 0, 199) )
        driver = OpenTunerDriver(cfg)

        unsearched = set(range(200))
        for i in range(20):
            cfg = driver.get_next_config()
            val = cfg.data["foo"]
            driver.report(time=val)
            unsearched.remove(val)
        self.assertEqual(len(unsearched), 180)
