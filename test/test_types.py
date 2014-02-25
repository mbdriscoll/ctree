import unittest
import ctypes as ct

from ctree.nodes.c import *

class TestTypeCodegen(unittest.TestCase):

  def test_void(self):    assert str(Void())   == "void"
  def test_char(self):    assert str(Char())   == "char"
  def test_short(self):   assert str(Short())  == "short"
  def test_int(self):     assert str(Int())    == "int"
  def test_float(self):   assert str(Float())  == "float"
  def test_long(self):    assert str(Long())   == "long"
  def test_double(self):  assert str(Double()) == "double"

  def test_unsigned_char(self):    assert str(UnsignedChar())   == "unsigned char"
  def test_unsigned_short(self):   assert str(UnsignedShort())  == "unsigned short"
  def test_unsigned_int(self):     assert str(UnsignedInt())    == "unsigned int"
  def test_unsigned_long(self):    assert str(UnsignedLong())   == "unsigned long"

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


class TestCtreeTypeToCtypeConversion(unittest.TestCase):

  def _check(self, tree, ctypes_type):
    self.assertEqual(tree.as_ctype(), ctypes_type)

  def test_void(self):
    self._check( Void(), ct.c_void_p )

  def test_char(self):
    self._check( Char(), ct.c_char )

  def test_uchar(self):
    self._check( UnsignedChar(), ct.c_ubyte )

  def test_short(self):
    self._check( Short(), ct.c_short )

  def test_ushort(self):
    self._check( UnsignedShort(), ct.c_ushort )

  def test_int(self):
    self._check( Int(), ct.c_int )

  def test_uint(self):
    self._check( UnsignedInt(), ct.c_uint )

  def test_float(self):
    self._check( Float(), ct.c_float )

  def test_double(self):
    self._check( Double(), ct.c_double )

  def test_longdouble(self):
    self._check( LongDouble(), ct.c_longdouble )

  def test_int_ptr(self):
    self._check( Ptr(Int()), \
                 ct.POINTER(ct.c_int) )

  def test_float_ptr(self):
    self._check( Ptr(Float()), \
                 ct.POINTER(ct.c_float) )

  def test_float_ptr_ptr(self):
    self._check( Ptr(Ptr(Float())), \
                 ct.POINTER(ct.POINTER(ct.c_float)) )

  def test_void_fn_void(self):
    self._check( FuncType(Void()), \
                 ct.CFUNCTYPE(ct.c_void_p) )

  def test_int_fn_void(self):
    self._check( FuncType(Int()), \
                 ct.CFUNCTYPE(ct.c_int) )

  def test_void_fn_int(self):
    self._check( FuncType(Void(), [Int()]), \
                 ct.CFUNCTYPE(ct.c_void_p, ct.c_int) )

  def test_int_fn_int(self):
    self._check( FuncType(Int(), [Int()]), \
                 ct.CFUNCTYPE(ct.c_int, ct.c_int) )

  def test_int_fn_int_float(self):
    self._check( FuncType(Int(), [Int(), Float()]), \
                 ct.CFUNCTYPE(ct.c_int, ct.c_int, ct.c_float) )
