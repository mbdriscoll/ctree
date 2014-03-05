import unittest

from ctree.c.nodes import *


class TestFunctionCalls(unittest.TestCase):
    def _check(self, tree, expected):
        actual = str(tree)
        self.assertEqual(actual, expected)

    def test_call_00(self):
        tree = FunctionCall(SymbolRef('fn'), [])
        self._check(tree, "fn()")

    def test_call_01(self):
        args = [SymbolRef("arg0")]
        tree = FunctionCall(SymbolRef('fn'), args)
        self._check(tree, "fn(arg0)")

    def test_call_02(self):
        args = [SymbolRef("arg0"), SymbolRef("arg1")]
        tree = FunctionCall(SymbolRef('fn'), args)
        self._check(tree, "fn(arg0, arg1)")
