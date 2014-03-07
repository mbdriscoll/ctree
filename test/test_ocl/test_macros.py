import unittest

from ctree.ocl.macros import *


class TestOclMacros(unittest.TestCase):
    def test_CL_SUCCESS(self):
      tree = CL_SUCCESS()
      self.assertEqual(tree.codegen(), "CL_SUCCESS")
