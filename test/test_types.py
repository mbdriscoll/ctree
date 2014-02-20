import unittest

from ctree.nodes import *

class TestTypes(unittest.TestCase):

  def test_void(self):    assert str(Void())   == "void"
  def test_char(self):    assert str(Char())   == "char"
  def test_int(self):     assert str(Int())    == "int"
  def test_float(self):   assert str(Float())  == "float"
  def test_long(self):    assert str(Long())   == "long"
  def test_double(self):  assert str(Double()) == "double"

  def test_void_ptr(self):    assert str(Ptr(Void()))   == "void*"
  def test_char_ptr(self):    assert str(Ptr(Char()))   == "char*"
  def test_int_ptr(self):     assert str(Ptr(Int()))    == "int*"
  def test_float_ptr(self):   assert str(Ptr(Float()))  == "float*"
  def test_long_ptr(self):    assert str(Ptr(Long()))   == "long*"
  def test_double_ptr(self):  assert str(Ptr(Double())) == "double*"

  def test_double_ptr_ptr(self):  assert str(Ptr(Ptr(Double()))) == "double**"

  def test_float_equality(self):
    self.assertEqual(Float(), Float())

  def test_unequality(self):
    self.assertNotEqual(Int(), Float())


class TestTypeFetcher(unittest.TestCase):

  def _check(self, tree, expected):
    actual = str(tree)
    self.assertEqual(actual, expected)

  def test_string_type(self):
    s = String("foo")
    self._check(s.get_type(), "char*")

  def test_int_type(self):
    n = Constant(123)
    self._check(n.get_type(), "int")

  def test_float_type(self):
    n = Constant(123.4)
    self._check(n.get_type(), "float")

  def test_char_type(self):
    n = Constant('b')
    self._check(n.get_type(), "char")

  def test_binop_add_intint(self):
    a, b = Constant(1), Constant(2)
    node = Add(a, b)
    self._check(node.get_type(), "int")

  def test_binop_add_floatfloat(self):
    a, b = Constant(1.3), Constant(2.4)
    node = Add(a, b)
    self._check(node.get_type(), "float")

  def test_binop_add_floatint(self):
    a, b = Constant(1.3), Constant(2)
    node = Add(a, b)
    self._check(node.get_type(), "float")

  def test_binop_add_intfloat(self):
    a, b = Constant(1), Constant(2.3)
    node = Add(a, b)
    self._check(node.get_type(), "float")

  def test_binop_add_charint(self):
    a, b = Constant('b'), Constant(2)
    node = Add(a, b)
    self._check(node.get_type(), "int")

  def test_binop_add_charfloat(self):
    a, b = Constant('b'), Constant(2.3)
    node = Add(a, b)
    self._check(node.get_type(), "float")
