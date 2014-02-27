from ctree.visitors import NodeVisitor
from ctree.analyses import DeclFinder
from ctree.nodes.c import *

from ctypes import *

class TypeFetcher(NodeVisitor):
  """
  Dynamically computes the type of the Expression.
  """
  def visit_String(self, node):
    return c_char_p

  def visit_SymbolRef(self, node):
    if node.type != None:
      return node.type
    else:
      #decl = DeclFinder().find(node)
      #return decl.get_type()
      return "??"

  def visit_Constant(self, node):
    n = node.value
    if   isinstance(n, str):   return c_char
    elif isinstance(n, int):   return c_long
    elif isinstance(n, float): return c_double
    else:
      raise Exception("Cannot determine type for Constant of type %s." % \
                      type(n).__class__)

  def visit_BinaryOp(self, node):
    lhs = self.visit(node.left)
    rhs = self.visit(node.right)
    if isinstance(node.op, (Op.Add, Op.Sub, Op.Mul, Op.Div, Op.Mod,
                            Op.BitAnd, Op.BitOr, Op.BitXor,
                            Op.BitShL, Op.BitShR)):
      return self._usual_arithmetic_convert(lhs, rhs)
    elif isinstance(node.op, (Op.Lt, Op.Gt, Op.LtE, Op.GtE, Op.Eq, Op.NotEq,
                              Op.And, Op.Or)):
      return c_int
    elif isinstance(node.op, Op.Comma):
      return rhs
    elif ininstance(node.op, Op.ArrayRef):
      return lhs.base
    else:
      raise Exception("Cannot determine return type of (%s %s %s)." % \
        (type(lhs).__name__, node.op, type(rhs).__name__))

  @staticmethod
  def _usual_arithmetic_convert(t0, t1):
    """
    Computes the return type of an arithmetic operator applied to arguments of
    the built-in numeric types.
    See C89 6.2.5.1.
    """
    if   t0 == c_longdouble or t1 == c_longdouble: return c_longdouble
    elif t0 == c_double     or t1 == c_double:     return c_double
    elif t0 == c_float      or t1 == c_float:      return c_float
    else:
      t0, t1 = TypeFetcher._integer_promote(t0), TypeFetcher._integer_promote(t1)
      if   t0 == c_ulong or t1 == c_ulong: return c_ulong
      elif t0 == c_long  or t1 == c_long : return c_long
      elif t0 == c_uint  or t1 == c_uint : return c_uint
      elif t0 == c_int   or t1 == c_int  : return c_int
      else:
        raise Exception("Failed to apply usual arith conversion (c89 6.2.1.5) to types: %s, %s." % \
                        (type(t0).__name__, type(t1).__name__))

  @staticmethod
  def _integer_promote(t):
    """
    Promote small types to integers accd to c89 6.2.1.1.
    """
    if issubclass(t, (c_int, c_uint, c_long, c_ulong)):
      return t
    elif issubclass(t, (c_char, c_ubyte, c_short, c_ushort)):
      return c_int
    else:
      raise Exception("Cannot promote type %s to an integer-type." % t)


# ---------------------------------------------------------------------------
# numpy-specific stuff

# FIXME we need an extensible way to register types for optional packages
# like numpy

try:
  import numpy as np
  _NUMPY_DTYPE_TO_CTYPE = {
    np.dtype('float64'): c_double,
    np.dtype('float32'): c_float,
    np.dtype('int64'):   c_long,
    np.dtype('int32'):   c_int,
    # TODO add the rest
  }
except ImportError:
  _NUMPY_DTYPE_TO_CTYPE = {}

def numpy_dtype_to_ctype(dtype):
  try:
    return _NUMPY_DTYPE_TO_CTYPE[dtype]
  except KeyError:
    raise Exception("Cannot convertion Numpy dtype '%s' to ctype." % dtype)

