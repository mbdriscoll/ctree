import unittest
import ctypes as ct

from ctree.c.nodes import *

class TestCastOps(unittest.TestCase):

  def setUp(self):
    self.foo = SymbolRef('foo')

  def _check(self, tree, expected):
    actual = str(tree)
    self.assertEqual(actual, expected)

  def test_void(self):
    tree = Cast(ct.c_void_p, self.foo)
    self._check(tree, "(void*) foo")

  def test_int(self):
    tree = Cast(ct.c_int, self.foo)
    self._check(tree, "(int) foo")

  def test_int_p(self):
    tree = Cast(ct.POINTER(ct.c_int), self.foo)
    self._check(tree, "(int*) foo")
