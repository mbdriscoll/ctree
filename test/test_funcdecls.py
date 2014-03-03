import unittest
import ctypes as ct

from ctree.nodes.c import *

class TestFuncDecls(unittest.TestCase):

  def _check(self, tree, expected):
    actual = str(tree)
    self.assertEqual(actual, expected)

  def test_voidvoid(self):
    node = FunctionDecl(ct.c_void_p, SymbolRef("foo"))
    self._check(node, "void* foo()")

  def test_intvoid(self):
    node = FunctionDecl(ct.c_int, SymbolRef("foo"))
    self._check(node, "int foo()")

  def test_voidint(self):
    params = [SymbolRef("a", ct.c_int)]
    node = FunctionDecl(ct.c_void_p, SymbolRef("foo"), params)
    self._check(node, "void* foo(int a)")

  def test_intint(self):
    params = [SymbolRef("b", ct.c_int)]
    node = FunctionDecl(ct.c_int, SymbolRef("foo"), params)
    self._check(node, "int foo(int b)")

  def test_voidintint(self):
    params = [SymbolRef("c", ct.c_int), SymbolRef("d", ct.c_int)]
    node = FunctionDecl(ct.c_void_p, SymbolRef("foo"), params)
    self._check(node, "void* foo(int c, int d)")

  def test_voidintint_names(self):
    params = [SymbolRef("bar", ct.c_int), SymbolRef('baz', ct.c_int)]
    node = FunctionDecl(ct.c_void_p, SymbolRef("foo"), params)
    self._check(node, "void* foo(int bar, int baz)")

  def test_withdefn(self):
    body = [Add(SymbolRef('foo'), SymbolRef('bar'))]
    node = FunctionDecl(ct.c_void_p, SymbolRef("fn"), defn=body)
    self._check(node, """void* fn() {
    foo + bar;
}""")
