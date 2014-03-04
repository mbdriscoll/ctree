import unittest
import ctypes as ct

from ctree.c.nodes import *

class TestVarDecls(unittest.TestCase):

  def _check(self, tree, expected):
    actual = str(tree)
    self.assertEqual(actual, expected)

  def test_simple_00(self):
    foo = SymbolRef('foo', type=ct.c_int)
    self._check(foo, "int foo")

  def test_simple_01(self):
    foo = Assign(SymbolRef('foo', type=ct.c_double), Constant(1.2))
    self._check(foo, "double foo = 1.2")
