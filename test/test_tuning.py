import unittest


class TestOpenTuner(unittest.TestCase):
    def test_import_opentuner(self):
        import ctree.tune

    def test_make_int_param(self):
        from ctree.tune import IntegerParameter

        IntegerParameter("block_size", 1, 10)
