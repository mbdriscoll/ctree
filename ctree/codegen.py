from ctree.visitors import NodeVisitor
from ctree.nodes import *

class CodeGenerator(NodeVisitor):
  """
  Return a string containing the program text.
  """
  def visit_UnaryOp(self, node):
    arg = self.visit(node.arg)
    if isinstance(node.op, (Op.PostInc, Op.PostDec)):
      return "%s%s" % (arg, node.op)
    else:
      return "%s%s" % (node.op, arg)

  def visit_BinaryOp(self, node):
    lhs = self.visit(node.left)
    rhs = self.visit(node.right)
    if isinstance(node.op, Op.Cast):
      return "(%s) %s" % (lhs, rhs)
    else:
      return "%s %s %s" % (lhs, node.op, rhs)

  def visit_Assign(self, node):
    target = self.visit(node.target)
    value = self.visit(node.value)
    return "%s = %s" % (target, value)

  def visit_AugAssign(self, node):
    lhs = self.visit(node.target)
    rhs = self.visit(node.value)
    return "%s %s= %s" % (lhs, node.op, rhs)

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
