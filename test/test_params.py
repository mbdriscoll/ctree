import ctypes
import unittest

from ctree.nodes.c import *

class TestParams(unittest.TestCase):

  def _check(self, tree, expected):
    actual = str(tree)
    self.assertEqual(actual, expected)

  def test_typename(self):
    nm = SymbolRef("foo")
    ty = ctypes.c_int
    node = Param(ty, nm)
    self._check(node, "int foo")

  def test_type(self):
    ty = ctypes.c_int
    node = Param(ty)
    self._check(node, "int")
