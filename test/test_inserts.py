import unittest
from textwrap import dedent

from ctree.c.nodes import *


class TestAstInsertion(unittest.TestCase):
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

    def test_insert_before_front(self):
        self.front.insert_before(SymbolRef("d"))
        self._check(self.block, """\
    {
        d;
        a;
        b;
        c;
    }""")

    def test_insert_after_front(self):
        self.front.insert_after(SymbolRef("d"))
        self._check(self.block, """\
    {
        a;
        d;
        b;
        c;
    }""")

    def test_insert_before_mid(self):
        self.mid.insert_before(SymbolRef("d"))
        self._check(self.block, """\
    {
        a;
        d;
        b;
        c;
    }""")

    def test_insert_after_mid(self):
        self.mid.insert_after(SymbolRef("d"))
        self._check(self.block, """\
    {
        a;
        b;
        d;
        c;
    }""")

    def test_insert_before_back(self):
        self.back.insert_before(SymbolRef("d"))
        self._check(self.block, """\
    {
        a;
        b;
        d;
        c;
    }""")

    def test_insert_after_back(self):
        self.back.insert_after(SymbolRef("d"))
        self._check(self.block, """\
    {
        a;
        b;
        c;
        d;
    }""")

    def test_bad_insert_before(self):
        with self.assertRaises(Exception):
            self.block.insert_before(SymbolRef("d"))

    def test_bad_insert_after(self):
        with self.assertRaises(Exception):
            self.block.insert_after(SymbolRef("d"))
