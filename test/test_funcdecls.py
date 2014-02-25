import unittest

from ctree.nodes.c import *

class TestFuncDecls(unittest.TestCase):

  def _check(self, tree, expected):
    actual = str(tree)
    self.assertEqual(actual, expected)

  def test_voidvoid(self):
    node = FunctionDecl(Void(), SymbolRef("foo"))
    self._check(node, "void foo()")

  def test_intvoid(self):
    node = FunctionDecl(Int(), SymbolRef("foo"))
    self._check(node, "int foo()")

  def test_voidint(self):
    params = [Param(Int())]
    node = FunctionDecl(Void(), SymbolRef("foo"), params)
    self._check(node, "void foo(int)")

  def test_intint(self):
    params = [Param(Int())]
    node = FunctionDecl(Int(), SymbolRef("foo"), params)
    self._check(node, "int foo(int)")

  def test_voidintint(self):
    params = [Param(Int()), Param(Int())]
    node = FunctionDecl(Void(), SymbolRef("foo"), params)
    self._check(node, "void foo(int, int)")

  def test_voidintint_names(self):
    params = [Param(Int(), SymbolRef('bar')), Param(Int(), SymbolRef('baz'))]
    node = FunctionDecl(Void(), SymbolRef("foo"), params)
    self._check(node, "void foo(int bar, int baz)")

  def test_withdefn(self):
    body = [Add(SymbolRef('foo'), SymbolRef('bar'))]
    node = FunctionDecl(Void(), SymbolRef("fn"), defn=body)
    self._check(node, """void fn() {
    foo + bar;
}""")
