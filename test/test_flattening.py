import unittest
from textwrap import dedent

from ctree.c.nodes import *
from ctree.analyses import *
from ctree.util import flatten, enumerate_flatten


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


class TestRawEnumeratedFlattening(unittest.TestCase):
    def _check(self, nested, exp_indices):
        act_indices, values = zip(*enumerate_flatten(nested))
        for actual, expected in zip(act_indices, exp_indices):
            self.assertTupleEqual(actual, expected)

    def test_obj(self):
        self._check(123, ())

    def test_flat(self):
        self._check([1, 2, 3], [(0,), (1,), (2,)])

    def test_lol(self):
        self._check([1, [2, 3]],   [(0,), (1,0), (1,1)])
        self._check([[1, 2], 3],   [(0,0), (0,1), (1,)])
        self._check([[1], 2, [3]], [(0,0), (1,), (2,0)])

    def test_lolol(self):
        self._check([1, [2, [3, 4]]], [(0,), (1,0), (1,1,0), (1,1,1)])
        self._check([[1, [2]], 3, 4], [(0,0), (0,1,0), (1,), (2,)])


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


@unittest.skip("fails")
class TestFlatteningDotGen(unittest.TestCase):
    def test_lol_1(self):
        tree = Block([[a, b]])
        tree.to_dot()
