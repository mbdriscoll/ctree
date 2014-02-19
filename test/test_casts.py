import unittest

from ctree.nodes import *

class TestCastOps(unittest.TestCase):

  def setUp(self):
    self.foo = SymbolRef('foo')

  def _check(self, tree, expected):
    actual = str(tree)
    self.assertEqual(actual, expected)

  def test_void(self):
    tree = Cast(Void(), self.foo)
    self._check(tree, "(void) foo")

  def test_void_p(self):
    tree = Cast(Ptr(Void()), self.foo)
    self._check(tree, "(void*) foo")

  def test_int(self):
    tree = Cast(Int(), self.foo)
    self._check(tree, "(int) foo")

  def test_int_p(self):
    tree = Cast(Ptr(Int()), self.foo)
    self._check(tree, "(int*) foo")
