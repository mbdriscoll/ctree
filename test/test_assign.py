import unittest

from ctree.c.nodes import *


class TestAssigns(unittest.TestCase):
    def setUp(self):
        self.foo, self.bar = SymbolRef("foo"), SymbolRef("bar")

    def test_simple_assign(self):
        node = Assign(self.foo, self.bar)
        self.assertEqual(str(node), "foo = bar")
