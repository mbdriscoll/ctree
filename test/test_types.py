import unittest
import ctypes

from ctree.nodes.c import *

class TestTypeProperties(unittest.TestCase):
  def test_float_equality(self):
    self.assertEqual(ctypes.c_float, ctypes.c_float)

  def test_unequality(self):
    self.assertNotEqual(ctypes.c_int, ctypes.c_float)


class TestTypeFetcher(unittest.TestCase):
  def _check(self, actual, expected):
    self.assertEqual(actual, expected)

  def test_string_type(self):
    s = String("foo")
    self._check(s.get_type(), ctypes.c_char_p)

  def test_int_type(self):
    n = Constant(123)
    self._check(n.get_type(), ctypes.c_long)

  def test_float_type(self):
    n = Constant(123.4)
    self._check(n.get_type(), ctypes.c_double)

  def test_char_type(self):
    n = Constant('b')
    self._check(n.get_type(), ctypes.c_char)

  def test_binop_add_intint(self):
    a, b = Constant(1), Constant(2)
    node = Add(a, b)
    self._check(node.get_type(), ctypes.c_long)

  def test_binop_add_floatfloat(self):
    a, b = Constant(1.3), Constant(2.4)
    node = Add(a, b)
    self._check(node.get_type(), ctypes.c_double)

  def test_binop_add_floatint(self):
    a, b = Constant(1.3), Constant(2)
    node = Add(a, b)
    self._check(node.get_type(), ctypes.c_double)

  def test_binop_add_intfloat(self):
    a, b = Constant(1), Constant(2.3)
    node = Add(a, b)
    self._check(node.get_type(), ctypes.c_double)

  def test_binop_add_charint(self):
    a, b = Constant('b'), Constant(2)
    node = Add(a, b)
    self._check(node.get_type(), ctypes.c_long)

  def test_binop_add_charfloat(self):
    a, b = Constant('b'), Constant(2.3)
    node = Add(a, b)
    self._check(node.get_type(), ctypes.c_double)

  def test_binop_compare(self):
    a, b = Constant('b'), Constant(2.3)
    node = Lt(a, b)
    self._check(node.get_type(), ctypes.c_int)

  def test_binop_compare(self):
    a, b = Constant('b'), Constant(2.3)
    node = Comma(a, b)
    self._check(node.get_type(), ctypes.c_double)

  def test_bad_constant(self):
    class nothing: pass
    a = Constant(nothing())
    with self.assertRaises(Exception):
      self._check(a.get_type(), ctypes.c_int)
