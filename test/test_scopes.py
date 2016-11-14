import unittest

from ctree.c.nodes import *


class TestBlocks(unittest.TestCase):
    def _check(self, tree, expected):
        actual = str(tree)
        self.assertEqual(actual, expected)

    def test_simple_00(self):
        body = [Constant(12), Constant('b')]
        tree = Block(body)
        self._check(tree, """\
{
    12;
    'b';
}""")

    def test_nested_00(self):
        a, b = SymbolRef("a"), Constant('b')
        tree = Block([Block([a, b, a]), b, a])
        self._check(tree, """\
{
    {
        a;
        'b';
        a;
    }
    'b';
    a;
}""")
