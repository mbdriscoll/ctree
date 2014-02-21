import unittest

from ctree.nodes import *

class TestVarDecls(unittest.TestCase):

  def _check(self, tree, expected):
    actual = str(tree)
    self.assertEqual(actual, expected)

  def test_simple_00(self):
    foo = SymbolRef('foo', type=Int())
    self._check(foo, "int foo")

  def test_simple_01(self):
    foo = Assign(SymbolRef('foo', type=Float()), Constant(1.2))
    self._check(foo, "float foo = 1.2")

  @unittest.skip("need to unparse name inside type")
  def test_simple_02(self):
    foo = SymbolRef('foo', type=FuncType(Void(), [Float()]))
    self._check(foo, "void (*foo)(float)")
