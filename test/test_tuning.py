import unittest

from itertools import islice

# class TestNullTuningDriver(unittest.TestCase):
#     def test_import(self):
#         import ctree.tune

#     def test_null_driver_stream(self):
#         from ctree.tune import NullTuningDriver

#         driver = NullTuningDriver()
#         for cfg in islice(driver.configs, 4):
#             self.assertDictEqual(cfg, {})

#     def test_null_driver_report(self):
#         from ctree.tune import NullTuningDriver

#         driver = NullTuningDriver()
#         for cfg in islice(driver.configs, 4):
#             driver.report(time=0.4)


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
        for cfg in islice(driver.configs, 20):
            val = cfg["foo"]
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
        )

        objective = MinimizeTime()
        params = [IntegerParameter("foo", 0, 100)]
        driver = BruteForceTuningDriver(params, objective)

        unsearched = set(range(0, 100))
        for config in islice(driver.configs, 100):
            unsearched.remove(config["foo"])
            driver.report(time=0.4)
        self.assertSetEqual(unsearched, set())

    def test_bruteforce_driver_2d(self):
        from ctree.tune import (
            BruteForceTuningDriver,
            IntegerParameter,
            MinimizeTime,
        )

        params = [
            IntegerParameter("foo", 0, 10),
            IntegerParameter("bar", 0, 10),
        ]
        driver = BruteForceTuningDriver(params, MinimizeTime())

        unsearched = set(range(0, 100))
        for config in islice(driver.configs, 100):
            entry = config["foo"] * 10 + config["bar"]
            unsearched.remove(entry)
            driver.report(time=0.4)
        self.assertSetEqual(unsearched, set())

    def test_bruteforce_driver_2d_parabola(self):
        from ctree.tune import (
            BruteForceTuningDriver,
            IntegerParameter,
            MinimizeTime,
        )

        params = [
            IntegerParameter("x", 0, 10),
            IntegerParameter("y", 0, 10),
        ]
        driver = BruteForceTuningDriver(params, MinimizeTime())

        for config in islice(driver.configs, 100):
            # report height on inverted paraboloid with global min at (3,4)
            x, y = config["x"], config["y"]
            z = (x-3)**2 + (y-4)**2 + 1
            driver.report(time=z)

        for config in islice(driver.configs, 10):
            self.assertEqual((config["x"], config["y"]), (3, 4))

    def test_bruteforce_driver_other_params(self):
        from ctree.tune import (
            BruteForceTuningDriver,
            IntegerParameter,
            BooleanParameter,
            EnumParameter,
            MinimizeTime,
        )

        params = [
            IntegerParameter("foo", 0, 10),
            BooleanParameter("bar"),
            EnumParameter("baz", ['monty', 'python', 'rocks']),
        ]
        driver = BruteForceTuningDriver(params, MinimizeTime())

        nConfigs = 10*2*3
        configs = list(islice(driver.configs, nConfigs))
        self.assertEqual(len(configs), nConfigs)
