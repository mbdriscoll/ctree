from ctypes import *

from util import CtreeTest
from ctree.c.nodes import *


class TestVarDecls(CtreeTest):
    def test_simple_00(self):
        tree = SymbolRef('foo', c_double())
        self._check_code(tree, "double foo")

    def test_simple_01(self):
        tree = Assign(SymbolRef('foo', c_double()), Constant(1.2))
        self._check_code(tree, "double foo = 1.2")
