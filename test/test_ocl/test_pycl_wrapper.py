import unittest

import pycl as cl

from ctree.ocl import get_context_from_device

class TestCacheContexts(unittest.TestCase):
	def test_simple_cache(self):
		devices = cl.clGetDeviceIDs()
		device = devices[-1]
		ctx1 = get_context_from_device(device)
		ctx2 = get_context_from_device(device)
		self.assertEqual(ctx1, ctx2)