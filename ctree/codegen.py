from ctree.visitors import NodeVisitor
from ctree.nodes import *

class CodeGenerator(NodeVisitor):
  """
  Return a string containing the program text.
  """
  def __init__(self):
    self._indent = 0

  # -------------------------------------------------------------------------
  # internal support methods

  def _tab(self):
    return "    " * self._indent

  def _genblock(self, forest):
    self._indent += 1
    body = self._tab() + (";\n%s" % self._tab()).join(map(self.visit, forest)) + ";\n"
    self._indent -= 1
    return "{\n%s%s}" % (body, self._tab())

  def _parentheses(self, node):
    """A format string that includes parentheses if needed."""
    return "(%s)" if self._requires_parentheses(node) else "%s"

  def _requires_parentheses(self, node):
    """
    Return True if the current precedence is less than the
    parent precedence.  If the precedences are equal, check whether the
    node's orientation to the parent matches associativity.  If it doesn't,
    enclose with parentheses.
    """
    parent = getattr(node, 'parent', None)
    if isinstance(  node, (UnaryOp, BinaryOp)) and \
       isinstance(parent, (UnaryOp, BinaryOp)):
      prec = node.op.get_precedence()
      parent_prec = parent.op.get_precedence()
      is_first_child = isinstance(parent, UnaryOp) or \
                      (isinstance(parent, BinaryOp) and node is parent.left)
      assoc_left = parent.op.is_left_associative()
      if (prec < parent_prec) or \
         (prec == parent_prec and ((assoc_left and not is_first_child) or \
                                   (not assoc_left and is_first_child))):
        return True
    return False


  # -------------------------------------------------------------------------
  # visitor methods

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
      s = "%s%s" % (arg, node.op)
    else:
      s = "%s%s" % (node.op, arg)
    return self._parentheses(node) % s

  def visit_BinaryOp(self, node):
    lhs = self.visit(node.left)
    rhs = self.visit(node.right)
    if isinstance(node.op, Op.Cast):
      s = "(%s) %s" % (lhs, rhs)
    elif isinstance(node.op, Op.ArrayRef):
      s = "%s[%s]" % (lhs, rhs)
    else:
      s = "%s %s %s" % (lhs, node.op, rhs)
    return self._parentheses(node) % s

  def visit_AugAssign(self, node):
    lhs = self.visit(node.target)
    rhs = self.visit(node.value)
    return "%s %s= %s" % (lhs, node.op, rhs)

  def visit_TernaryOp(self, node):
    cond = self.visit(node.cond)
    then = self.visit(node.then)
    elze = self.visit(node.elze)
    s = "%s ? %s : %s" % (cond, then, elze)
    return self._parentheses(node) % s

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
    if node.decl_type:
      return "%s %s" % (node.get_type(), node.name)
    else:
      return str(node.name)

  def visit_Block(self, node):
     return self._genblock(node.body)

  def visit_Void(self, node):            return "void"
  def visit_Char(self, node):            return "char"
  def visit_Short(self, node):           return "short"
  def visit_Int(self, node):             return "int"
  def visit_Long(self, node):            return "long"

  def visit_UnsignedChar(self, node):    return "unsigned char"
  def visit_UnsignedShort(self, node):   return "unsigned short"
  def visit_UnsignedInt(self, node):     return "unsigned int"
  def visit_UnsignedLong(self, node):    return "unsigned long"

  def visit_Float(self, node):           return "float"
  def visit_Double(self, node):          return "double"
  def visit_LongDouble(self, node):      return "long double"

  def visit_Ptr(self, node):
    return "%s*" % self.visit(node.base)

  def visit_FuncType(self, node):
    args = ",".join(map(self.visit, node.arg_types))
    return "%s (*)(%s)" % (node.return_type, args)

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

  def visit_For(self, node):
    init = self.visit(node.init)
    test = self.visit(node.test)
    incr = self.visit(node.incr)
    body = self._genblock(node.body)
    return "for (%s; %s; %s) %s" % (init, test, incr, body)

  def visit_FunctionCall(self, node):
    func = self.visit(node.func)
    args = ", ".join(map(self.visit, node.args))
    return "%s(%s)" % (func, args)

  def visit_String(self, node):
    return '"%s"' % node.value
