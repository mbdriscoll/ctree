import unittest

from ctree.c.nodes import *
from ctree.c.types import *


class TestVarDecls(unittest.TestCase):
    def _check(self, tree, expected):
        actual = str(tree)
        self.assertEqual(actual, expected)

    def test_simple_00(self):
        foo = SymbolRef('foo', sym_type=Int())
        self._check(foo, "int foo")

    def test_simple_01(self):
        foo = Assign(SymbolRef('foo', sym_type=Double()), Constant(1.2))
        self._check(foo, "double foo = 1.2")
