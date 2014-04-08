import unittest

from ctree.c.nodes import *


class TestSymbols(unittest.TestCase):
    def test_symbolref(self):
        ref = SymbolRef("foo")
        assert str(ref) == "foo"

    def test_init_local(self):
        ref = SymbolRef("foo", _local=True)
        assert str(ref) == "__local foo"

    def test_init_const(self):
        ref = SymbolRef("foo", _const=True)
        assert str(ref) == "const foo"

    def test_set_local(self):
        ref = SymbolRef("foo")
        ref.set_local()
        assert str(ref) == "__local foo"

    def test_set_const(self):
        ref = SymbolRef("foo")
        ref.set_const()
        assert str(ref) == "const foo"
