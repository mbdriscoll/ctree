import unittest

from ctree.nodes import *
from ctree.c.nodes import *
from ctree.c.types import Int


class TestCtreeNode(unittest.TestCase):

    def test_get_root(self):
        a = SymbolRef('a')
        b = SymbolRef('b')
        root = Add(a, b)
        self.assertEqual(a.get_root(), root)

    def test_bad_override_codegen(self):
        class BadNode(CtreeNode):
            pass
        with self.assertRaises(Exception):
            BadNode().codegen()

    def test_bad_override_to_dot(self):
        class BadNode(CtreeNode):
            pass
        with self.assertRaises(Exception):
            BadNode()._to_dot()

    def test_find_all_attr_error(self):
        tree = Add(SymbolRef('a'), Constant(10))
        try:
            tree.find_all(SymbolRef, type=Int())
        except AttributeError:
            self.fail("find_all should not raise AttributeError")