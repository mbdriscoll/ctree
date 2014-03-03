import unittest
import ctypes as ct

from ctree.nodes.c import *

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

  @unittest.skip("need to unparse name inside type")
  def test_simple_02(self):
    foo = SymbolRef('foo', type=FuncType(ct.c_void_p, [ct.c_double]))
    self._check(foo, "void (*foo)(double)")
