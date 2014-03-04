import ctypes
from __future__ import print_function

from ctree.types import CtreeType, CtreeTypeResolver, TypeFetcher, get_ctree_type

class CType(CtreeType):
  """Base class for all built-in CTypes."""
  def codegen(self):
    from ctree.c.codegen import CCodeGen
    return CCodeGen().visit(self)

  def dotgen(self):
    from ctree.c.dotgen import CDotGen
    return CDotGen().visit(self)

  def as_ctype(self):
    return self._ctype

class Void(CType):   _ctype = ctypes.c_void_p
class Char(CType):   _ctype = ctypes.c_char
class UChar(CType):  _ctype = ctypes.c_ubyte
class Short(CType):  _ctype = ctypes.c_short
class UShort(CType): _ctype = ctypes.c_ushort
class Int(CType):    _ctype = ctypes.c_int
class UInt(CType):   _ctype = ctypes.c_uint
class Long(CType):   _ctype = ctypes.c_long
class ULong(CType):  _ctype = ctypes.c_ulong

class Float(CType):  _ctype = ctypes.c_float
class Double(CType): _ctype = ctypes.c_double
class LongDouble(CType): _ctype = ctypes.c_longdouble

class Ptr(CType):
  _fields = ['base_type']
  def __init__(self, base_type=Void()):
    self.base_type = base_type

class FuncType(CType):
  _fields = ['return_type', 'arg_types']
  def __init__(self, return_type=Void(), arg_types=[]):
    self.return_type = return_type
    self.arg_types = arg_types

  def as_ctype(self):
    return_ctype = self.return_type.as_ctype()
    arg_ctypes = [arg_type.as_ctype() for arg_type in self.arg_types]
    return ctypes.CFUNCTYPE(return_ctype, *arg_ctypes)


class NdPointer(CType):
  def __init__(self, dtype=None, ndim=1, shape=1, flags=None):
    from numpy.ctypeslib import ndpointer
    self.ptr = ndpointer(dtype, ndim, shape, flags)

  def as_ctype(self):
    return self.ptr


class CTypeResolver(CtreeTypeResolver):
  @staticmethod
  def resolve(obj):
    if   isinstance(obj, int):   return Long()
    elif isinstance(obj, float): return Double()
    elif isinstance(obj, str):
      return Char() if len(obj) == 1 else Ptr(Char())
    print ("resolve %s" % repr(obj))


class NumpyTypeResolver(CtreeTypeResolver):
  @staticmethod
  def resolve(ty):
    import numpy as np
    if   ty == np.int32: return Int()
    elif ty == np.int64: return Long()
    elif ty == np.float32: return Float()
    elif ty == np.float64: return Double()


class CTypeFetcher(TypeFetcher):
  """
  Dynamically computes the type of the Expression.
  """
  def visit_String(self, node):
    return Ptr(Char())

  def visit_SymbolRef(self, node):
    if node.type != None:
      return node.type
    else:
      #decl = DeclFinder().find(node)
      #return decl.get_type()
      return "??"

  def visit_Constant(self, node):
    return get_ctree_type( node.value )

  def visit_BinaryOp(self, node):
    from ctree.c.nodes import Op
    lhs = node.left.get_type()
    rhs = node.right.get_type()
    if isinstance(node.op, (Op.Add, Op.Sub, Op.Mul, Op.Div, Op.Mod,
                            Op.BitAnd, Op.BitOr, Op.BitXor,
                            Op.BitShL, Op.BitShR)):
      return self._usual_arithmetic_convert(lhs, rhs)
    elif isinstance(node.op, (Op.Lt, Op.Gt, Op.LtE, Op.GtE, Op.Eq, Op.NotEq,
                              Op.And, Op.Or)):
      return Int()
    elif isinstance(node.op, Op.Comma):
      return rhs
    elif isinstance(node.op, Op.ArrayRef):
      return lhs.base
    else:
      raise Exception("Cannot determine return type of (%s %s %s)." % \
        (lhs, node.op, rhs))

  @staticmethod
  def _usual_arithmetic_convert(t0, t1):
    """
    Computes the return type of an arithmetic operator applied to arguments of
    the built-in numeric types.
    See C89 6.2.5.1.
    """

    if   t0 == LongDouble() or t1 == LongDouble(): return LongDouble()
    elif t0 == Double()     or t1 == Double():     return Double()
    elif t0 == Float()      or t1 == Float():      return Float()
    else:
      t0 = CTypeFetcher._integer_promote(t0)
      t1 = CTypeFetcher._integer_promote(t1)
      if   t0 == ULong() or t1 == ULong(): return ULong()
      elif t0 == Long()  or t1 == Long() : return Long()
      elif t0 == UInt()  or t1 == UInt() : return UInt()
      elif t0 == Int()   or t1 == Int()  : return Int()
      else:
        raise Exception("Failed to apply usual arith conversion (c89 6.2.1.5) to types: %s, %s." % \
                        (t0, t1))

  @staticmethod
  def _integer_promote(t):
    """
    Promote small types to integers accd to c89 6.2.1.1.
    """
    if isinstance(t, (Int, UInt, Long, ULong)):
      return t
    elif isinstance(t, (Char, UChar, Short, UShort)):
      return Int()
    else:
      raise Exception("Cannot promote type %s to an integer-type." % t)


