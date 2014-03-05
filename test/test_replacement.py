import unittest
from textwrap import dedent

from ctree.c.nodes import *


class TestAstListReplacement(unittest.TestCase):
    def setUp(self):
        self.front = SymbolRef("a")
        self.mid = SymbolRef("b")
        self.back = SymbolRef("c")
        self.block = Block([
            self.front,
            self.mid,
            self.back,
        ])

    def _check(self, tree, expected_i):
        actual = str(tree)
        expected = dedent(expected_i)
        self.assertEqual(actual, expected)

    def test_replace_list_front(self):
        self.front.replace(SymbolRef("d"))
        self._check(self.block, """\
    {
        d;
        b;
        c;
    }""")

    def test_replace_list_middle(self):
        self.mid.replace(SymbolRef("d"))
        self._check(self.block, """\
    {
        a;
        d;
        c;
    }""")

    def test_replace_list_back(self):
        self.back.replace(SymbolRef("d"))
        self._check(self.block, """\
    {
        a;
        b;
        d;
    }""")

    def test_bad_replace(self):
        with self.assertRaises(Exception):
            self.block.replace(SymbolRef("d"))


class TestAstFieldReplacement(unittest.TestCase):
    def setUp(self):
        self.lhs = SymbolRef("a")
        self.rhs = SymbolRef("b")
        self.binop = Add(self.lhs, self.rhs)

    def _check(self, tree, expected_i):
        actual = str(tree)
        expected = dedent(expected_i)
        self.assertEqual(actual, expected)

    def test_replace_field_rhs(self):
        self.rhs.replace(SymbolRef("x"))
        self._check(self.binop, "a + x")

    def test_replace_field_lhs(self):
        self.lhs.replace(SymbolRef("x"))
        self._check(self.binop, "x + b")

    def test_bad_replace(self):
        with self.assertRaises(Exception):
            self.binop.replace(SymbolRef("d"))
