from ctree.visitors import NodeVisitor
from ctree.nodes import *

class TypeFetcher(NodeVisitor):
  """
  Dynamically computes the type of the Expression.
  """
  def visit_String(self, node):
    return Ptr(Char())

  def visit_SymbolRef(self, node):
    if node.decl_type != None:
      return node.decl_type
    else:
      # TODO traverse tree
      return Unknown()

  def visit_Constant(self, node):
    n = node.value
    if isinstance(n, str):
      return Char()
    elif isinstance(n, int):
      # TODO: handle long, unsigned, etc.
      return Int()
    elif isinstance(n, float):
      # TODO: handle double
      return Float()
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
      return Int()
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
    if   t0 == LongDouble() or t1 == LongDouble(): return LongDouble()
    elif t0 == Double()     or t1 == Double():     return Double()
    elif t0 == Float()      or t1 == Float():      return Float()
    else:
      t0, t1 = TypeFetcher._integer_promote(t0), TypeFetcher._integer_promote(t1)
      if   t0 == UnsignedLong() or t1 == UnsignedLong(): return UnsignedLong()
      elif t0 == Long()         or t1 == Long()        : return Long()
      elif t0 == UnsignedInt()  or t1 == UnsignedInt() : return UnsignedInt()
      elif t0 == Int()          or t1 == Int()         : return Int()
      else:
        raise Exception("Failed to apply usual arith conversion (c89 6.2.1.5) to types: %s, %s." % \
                        (type(t0).__name__, type(t1).__name__))

  @staticmethod
  def _integer_promote(t):
    """
    Promote small types to integers accd to c89 6.2.1.1.
    """
    if isinstance(t, (Int, UnsignedInt, Long, UnsignedLong)):
      return t
    elif isinstance(t, (Char, UnsignedChar, Short, UnsignedShort)):
      return Int()
    else:
      raise Exception("Cannot promote type %s to an integer-type." % type(t).__name__)
