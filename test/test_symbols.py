import unittest

from ctree.nodes.c import *

class TestSymbols(unittest.TestCase):

  def test_symbolref(self):
    ref = SymbolRef("foo")
    assert str(ref) == "foo"
