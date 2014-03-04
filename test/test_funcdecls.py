import unittest

from ctree.c.nodes import *
from ctree.c.types import *

class TestFuncDecls(unittest.TestCase):

  def _check(self, tree, expected):
    actual = str(tree)
    self.assertEqual(actual, expected)

  def test_voidvoid(self):
    node = FunctionDecl(Ptr(Void()), SymbolRef("foo"))
    self._check(node, "void* foo()")

  def test_intvoid(self):
    node = FunctionDecl(Int(), SymbolRef("foo"))
    self._check(node, "int foo()")

  def test_voidint(self):
    params = [SymbolRef("a", Int())]
    node = FunctionDecl(Ptr(Void()), SymbolRef("foo"), params)
    self._check(node, "void* foo(int a)")

  def test_intint(self):
    params = [SymbolRef("b", Int())]
    node = FunctionDecl(Int(), SymbolRef("foo"), params)
    self._check(node, "int foo(int b)")

  def test_voidintint(self):
    params = [SymbolRef("c", Int()), SymbolRef("d", Int())]
    node = FunctionDecl(Ptr(Void()), SymbolRef("foo"), params)
    self._check(node, "void* foo(int c, int d)")

  def test_voidintint_names(self):
    params = [SymbolRef("bar", Int()), SymbolRef('baz', Int())]
    node = FunctionDecl(Ptr(Void()), SymbolRef("foo"), params)
    self._check(node, "void* foo(int bar, int baz)")

  def test_withdefn(self):
    body = [Add(SymbolRef('foo'), SymbolRef('bar'))]
    node = FunctionDecl(Ptr(Void()), SymbolRef("fn"), defn=body)
    self._check(node, """void* fn() {
    foo + bar;
}""")
