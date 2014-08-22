import unittest

import pycl as cl

from ctree.ocl import get_context_and_queue_from_devices


class TestCacheContexts(unittest.TestCase):
    def test_simple_cache(self):
        devices = cl.clGetDeviceIDs()
        device = devices[-1]
        results1 = get_context_and_queue_from_devices([device])
        results2 = get_context_and_queue_from_devices([device])
        self.assertEqual(results1, results2)
