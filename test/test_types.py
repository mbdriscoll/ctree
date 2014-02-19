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
