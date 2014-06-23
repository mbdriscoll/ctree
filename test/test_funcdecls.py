from util import CtreeTest

from ctypes import *
from ctree.c.nodes import *


class TestFuncDecls(CtreeTest):
    def test_voidvoid(self):
        node = FunctionDecl(c_void_p(), SymbolRef("foo"))
        self._check_code(node, "void* foo()")

    def test_intvoid(self):
        node = FunctionDecl(c_int(), SymbolRef("foo"))
        self._check_code(node, "int foo()")

    def test_voidint(self):
        params = [SymbolRef("a", c_int())]
        node = FunctionDecl(c_void_p(), SymbolRef("foo"), params)
        self._check_code(node, "void* foo(int a)")

    def test_intint(self):
        params = [SymbolRef("b", c_int())]
        node = FunctionDecl(c_int(), SymbolRef("foo"), params)
        self._check_code(node, "int foo(int b)")

    def test_voidintint(self):
        params = [SymbolRef("c", c_int()), SymbolRef("d", c_int())]
        node = FunctionDecl(c_void_p(), SymbolRef("foo"), params)
        self._check_code(node, "void* foo(int c, int d)")

    def test_voidintint_names(self):
        params = [SymbolRef("bar", c_int()), SymbolRef('baz', c_int())]
        node = FunctionDecl(c_void_p(), SymbolRef("foo"), params)
        self._check_code(node, "void* foo(int bar, int baz)")

    def test_withdefn(self):
        body = [Add(SymbolRef('foo'), SymbolRef('bar'))]
        node = FunctionDecl(c_void_p(), SymbolRef("fn"), defn=body)
        self._check_code(node, """\
        void* fn() {
            foo + bar;
        }""")

    def test_set_kernel(self):
        params = [SymbolRef("bar", c_int()), SymbolRef('baz', c_int())]
        node = FunctionDecl(c_void_p(), SymbolRef("foo"), params)
        node.set_kernel();
        self._check_code(node, "__kernel void* foo(int bar, int baz)")
