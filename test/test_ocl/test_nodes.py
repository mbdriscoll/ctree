import unittest

from ctree.ocl.nodes import *


class TestOclNodes(unittest.TestCase):
    def test_file(self):
      f = OclFile("kernel", [])
      self.assertEqual(f.codegen(), "// <file: kernel.cl>\n")
