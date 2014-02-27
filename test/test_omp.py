import unittest

from ctree.nodes.omp import *

class TestOmpCodegen(unittest.TestCase):
  def test_parallel(self):
    node = OmpParallel()
    self.assertEqual(str(node), "#pragma omp parallel")
