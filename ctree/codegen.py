from ctree.visitors import NodeVisitor
from ctree.nodes import *

class CodeGenerator(NodeVisitor):
  """
  Return a string containing the program text.
  """
  def visit_UnaryOp(self, node, op):
    if isinstance(node, (PostInc, PostDec)):
      return "%s%s" % (node.arg, op)
    else:
      return "%s%s" % (op, node.arg)

  def visit_Plus(self, node):    return self.visit_UnaryOp(node, "+")
  def visit_Minus(self, node):   return self.visit_UnaryOp(node, "-")
  def visit_Not(self, node):     return self.visit_UnaryOp(node, "!")
  def visit_BitNot(self, node):  return self.visit_UnaryOp(node, "~")
  def visit_PreInc(self, node):  return self.visit_UnaryOp(node, "++")
  def visit_PreDec(self, node):  return self.visit_UnaryOp(node, "--")
  def visit_PostInc(self, node): return self.visit_UnaryOp(node, "++")
  def visit_PostDec(self, node): return self.visit_UnaryOp(node, "--")
  def visit_Ref(self, node):     return self.visit_UnaryOp(node, "&")
  def visit_Deref(self, node):   return self.visit_UnaryOp(node, "*")

  def visit_BinaryOp(self, node, op):
    lhs = self.visit(node.left)
    rhs = self.visit(node.right)
    return "%s %s %s" % (lhs, op, rhs)

  def visit_Add(self, node):     return self.visit_BinaryOp(node, "+")
  def visit_Sub(self, node):     return self.visit_BinaryOp(node, "-")
  def visit_Mul(self, node):     return self.visit_BinaryOp(node, "*")
  def visit_Div(self, node):     return self.visit_BinaryOp(node, "/")
  def visit_Mod(self, node):     return self.visit_BinaryOp(node, "%")
  def visit_Gt(self, node):      return self.visit_BinaryOp(node, ">")
  def visit_Lt(self, node):      return self.visit_BinaryOp(node, "<")
  def visit_GtE(self, node):     return self.visit_BinaryOp(node, ">=")
  def visit_LtE(self, node):     return self.visit_BinaryOp(node, "<=")
  def visit_Eq(self, node):      return self.visit_BinaryOp(node, "==")
  def visit_NotEq(self, node):   return self.visit_BinaryOp(node, "!=")
  def visit_BitAnd(self, node):  return self.visit_BinaryOp(node, "&")
  def visit_BitOr(self, node):   return self.visit_BinaryOp(node, "|")
  def visit_BitShL(self, node):  return self.visit_BinaryOp(node, "<<")
  def visit_BitShR(self, node):  return self.visit_BinaryOp(node, ">>")
  def visit_BitXor(self, node):  return self.visit_BinaryOp(node, "^")
  def visit_And(self, node):     return self.visit_BinaryOp(node, "&&")
  def visit_Or(self, node):      return self.visit_BinaryOp(node, "||")
  def visit_Comma(self, node):   return self.visit_BinaryOp(node, ",")

  def visit_Assign(self, node):
    target = self.visit(node.target)
    value = self.visit(node.value)
    return "%s = %s" % (target, value)

  def visit_AugAssign(self, node, op):
    lhs = self.visit(node.target)
    rhs = self.visit(node.value)
    return "%s %s %s" % (lhs, op, rhs)

  def visit_AddAssign(self, node):     return self.visit_AugAssign(node, "+=")
  def visit_SubAssign(self, node):     return self.visit_AugAssign(node, "-=")
  def visit_MulAssign(self, node):     return self.visit_AugAssign(node, "*=")
  def visit_DivAssign(self, node):     return self.visit_AugAssign(node, "/=")
  def visit_ModAssign(self, node):     return self.visit_AugAssign(node, "%=")
  def visit_BitAndAssign(self, node):  return self.visit_AugAssign(node, "&=")
  def visit_BitOrAssign(self, node):   return self.visit_AugAssign(node, "|=")
  def visit_BitXorAssign(self, node):  return self.visit_AugAssign(node, "^=")
  def visit_BitShLAssign(self, node):  return self.visit_AugAssign(node, "<<=")
  def visit_BitShRAssign(self, node):  return self.visit_AugAssign(node, ">>=")

  def visit_TernaryOp(self, node):
    cond = self.visit(node.cond)
    then = self.visit(node.then)
    elze = self.visit(node.elze)
    return "%s ? %s : %s" % (cond, then, elze)

  def visit_Cast(self, node):
    type = self.visit(node.type)
    value = self.visit(node.value)
    return "(%s) %s" % (type, value)

  def visit_Constant(self, node):
    if isinstance(node.value, str):
      return "'%s'" % node.value[0]
    else:
      return str(node.value)

  def visit_SymbolRef(self, node):
    return str(node.name)

  def visit_Void(self, node):    return "void"
  def visit_Char(self, node):    return "char"
  def visit_Int(self, node):     return "int"
  def visit_Float(self, node):   return "float"
  def visit_Long(self, node):    return "long"
  def visit_Double(self, node):  return "double"

  def visit_Ptr(self, node):
    return "%s*" % self.visit(node.base)
