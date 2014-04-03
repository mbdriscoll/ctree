import unittest

from ctree.c.nodes import *


class TestBinaryOps(unittest.TestCase):
    def _check(self, node, expected_string):
        self.assertEqual(str(node), expected_string)

    def test_simple_macro(self):
        node = Define("test_macro", ["d1, d2"], "d1 + d2")
        self._check(node, "#define test_macro(d1, d2) d1 + d2")

    def test_no_args(self):
        node = Define("test_macro", [], "39")
        self._check(node, "#define test_macro() 39")
