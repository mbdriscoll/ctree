from ctree.visitors import NodeVisitor
from ctree.nodes import *

class CodeGenerator(NodeVisitor):
  """
  Return a string containing the program text.
  """
  def __init__(self):
    self._indent = 0

  def tab(self):
    return "    " * self._indent

  def increase_indent(self):
    return self

  def __enter__(self):
    self._indent += 1
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self._indent -= 1

  def _genblock(self, forest):
    with self.increase_indent():
      body = self.tab() + (";\n%s" % self.tab()).join(map(self.visit, forest)) + ";\n"
    return "{\n%s%s}" % (body, self.tab())

  def visit_FunctionDecl(self, node):
    rettype = self.visit(node.return_type)
    name = self.visit(node.name)
    params = ", ".join(map(self.visit, node.params))
    if node.defn:
      defn = self._genblock(node.defn)
      return "%s %s(%s) %s" % (rettype, name, params, defn)
    else:
      return "%s %s(%s)" % (rettype, name, params)

  def visit_Param(self, node):
    ty = self.visit(node.type)
    if node.name != None:
      return "%s %s" % (ty, self.visit(node.name))
    else:
      return "%s" % ty

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
    elif isinstance(node.op, Op.ArrayRef):
      return "%s[%s]" % (lhs, rhs)
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

  def visit_Return(self, node):
    if node.value:
      return "return %s" % self.visit(node.value)
    else:
      return "return"

  def visit_If(self, node):
    cond = self.visit(node.cond)
    then = self._genblock(node.then)
    if node.elze:
      elze = self._genblock(node.elze)
      return "if (%s) %s else %s" % (cond, then, elze)
    else:
      return "if (%s) %s" % (cond, then)

  def visit_While(self, node):
    cond = self.visit(node.cond)
    body = self._genblock(node.body)
    return "while (%s) %s" % (cond, body)

  def visit_DoWhile(self, node):
    body = self._genblock(node.body)
    cond = self.visit(node.cond)
    return "do %s while (%s)" % (body, cond)
