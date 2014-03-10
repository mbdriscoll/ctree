import unittest


class TestOpenTuner(unittest.TestCase):
    def test_import(self):
        import ctree.tune

    def test_import_opentuner(self):
        import ctree.opentuner

    def test_make_int_param(self):
        from ctree.opentuner.driver import IntegerParameter

        IntegerParameter("block_size", 1, 10)
