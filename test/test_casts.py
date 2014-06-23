from util import CtreeTest

from ctypes import *
from ctree.c.nodes import *


class TestCastOps(CtreeTest):
    def setUp(self):
        self.foo = SymbolRef('foo')

    def test_void(self):
        tree = Cast(c_void_p(), self.foo)
        self._check_code(tree, "(void*) foo")

    def test_int(self):
        tree = Cast(c_long(), self.foo)
        self._check_code(tree, "(long) foo")

    def test_int_p(self):
        tree = Cast(POINTER(c_long)(), self.foo)
        self._check_code(tree, "(long*) foo")
