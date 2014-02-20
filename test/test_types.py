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
