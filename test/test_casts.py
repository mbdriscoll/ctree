from ctypes import *

from util import CtreeTest
from ctree.c.nodes import *


class TestCastOps(CtreeTest):
    def setUp(self):
        self.foo = SymbolRef('foo')

    def test_void(self):
        tree = Cast(c_void_p(), self.foo)
        self._check_code(tree, "(void*) foo")

    def test_int(self):
        tree = Cast(c_int(), self.foo)
        self._check_code(tree, "(int) foo")

    def test_int_p(self):
        tree = Cast(POINTER(c_int)(), self.foo)
        self._check_code(tree, "(int*) foo")
