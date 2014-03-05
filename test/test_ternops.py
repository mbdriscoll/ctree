import unittest

from ctree.c.nodes import *


class TestTernaryOps(unittest.TestCase):
    def setUp(self):
        self.foo = SymbolRef("foo")
        self.bar = SymbolRef("bar")
        self.baz = SymbolRef("baz")

    def test_ternary_op(self):
        node = TernaryOp(self.foo, self.bar, self.baz)
        self.assertEqual(str(node), "foo ? bar : baz")
