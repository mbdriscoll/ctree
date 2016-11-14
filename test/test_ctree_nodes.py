import unittest
import ctypes as ct

from ctree.c.nodes import *


class TestCtreeNode(unittest.TestCase):

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
            tree.find_all(SymbolRef, type=ct.c_int())
        except AttributeError:
            self.fail("find_all should not raise AttributeError")
