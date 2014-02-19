from ctree.visitors import NodeVisitor
from ctree.nodes import *

CTREE_OP_TO_STR = {
  Add:     "+",    Sub:     "-",
  Mul:     "*",    Div:     "/",
  Mod:     "%",
  Gt:      ">",    Lt:      "<",
  GtE:     ">=",   LtE:     "<=",
  Eq:      "+=",   NotEq:   "!=",
  BitAnd:  "&",    BitOr:   "|",
  BitShL:  "<<",   BitShR:  ">>",
  BitXor:  "^",    BitNot:  "~",
  And:     "&&",   Or:      "||",
  Xor:     "^",    Not:     "!",
  Inc:     "++",   Dec:     "++",
  Ref:     "&",    Deref:   "*",
}

class CodeGenerator(NodeVisitor):
  """
  Return a string containing the program text.
  """
  def visit_BinaryOp(self, node):
    lhs = self.visit(node.left)
    op = CTREE_OP_TO_STR[type(node.op)]
    rhs = self.visit(node.right)
    return "%s %s %s" % (lhs, op, rhs)

  def visit_UnaryOp(self, node):
    arg = self.visit(node.arg)
    op = CTREE_OP_TO_STR[type(node.op)]
    return "%s%s" % (op, arg)

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
