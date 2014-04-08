import unittest
from textwrap import dedent

from ctree.c.nodes import *
from ctree.analyses import *
from ctree.frontend import get_ast
from ctree.dotgen import to_dot

from ctree.util import flatten


a = SymbolRef("a")
b = SymbolRef("b")
c = SymbolRef("c")

class TestRawFlattening(unittest.TestCase):
    def _check(self, nested, flat):
        actual, expected = list(flatten(nested)), flat
        self.assertListEqual(actual, expected)

    def test_obj(self):
        self._check(123, [123])

    def test_flat(self):
        self._check([1, 2, 3], [1, 2, 3])

    def test_lol(self):
        self._check([1, [2, 3]],   [1, 2, 3])
        self._check([[1, 2], 3],   [1, 2, 3])
        self._check([[1], 2, [3]], [1, 2, 3])

    def test_lolol(self):
        self._check([1, [2, [3, 4]]], [1, 2, 3, 4])
        self._check([[1, [2]], 3, 4], [1, 2, 3, 4])


class TestListFlattening(unittest.TestCase):
    def _check(self, tree, expected):
        actual = str(tree)
        self.assertEqual(actual, dedent(expected))

    def test_flat_1(self):
        tree = Block([a])
        self._check(tree, """\
        {
            a;
        }""")

    def test_flat_3(self):
        tree = Block([a, b, c])
        self._check(tree, """\
        {
            a;
            b;
            c;
        }""")

    def test_lol_1(self):
        tree = Block([[a]])
        self._check(tree, """\
        {
            a;
        }""")

    def test_lol_3(self):
        tree = Block([[a, b], c])
        self._check(tree, """\
        {
            a;
            b;
            c;
        }""")

    def test_lolol_3(self):
        tree = Block([[a, b], [[[c]]]])
        self._check(tree, """\
        {
            a;
            b;
            c;
        }""")


class TestFlatteningDotGen(unittest.TestCase):
    def test_lol_1(self):
        tree = Block([[a, b]])
        to_dot(tree)
