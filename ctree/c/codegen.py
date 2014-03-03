"""
Code generator for C constructs.
"""

import ctypes as ct
from ctree.ast import CtreeNode
from ctree.codegen import CodeGenVisitor
from ctree.c.nodes import *
from ctree.precedence import *


class CCodeGen(CodeGenVisitor):
  """
  Manages generation of C code.
  """
  def _requires_parentheses(self, node):
    """
    Return True if the current precedence is less than the
    parent precedence.  If the precedences are equal, check whether the
    node's orientation to the parent matches associativity.  If it doesn't,
    enclose with parentheses.
    """
    parent = getattr(node, 'parent', None)
    if isinstance(  node, (UnaryOp, BinaryOp, TernaryOp)) and \
       isinstance(parent, (UnaryOp, BinaryOp, TernaryOp)):
      prec = get_precedence(node)
      parent_prec = get_precedence(parent)
      is_not_last_child = isinstance(parent, UnaryOp) or \
                      (isinstance(parent, BinaryOp) and node is parent.left) or \
                      (isinstance(parent, TernaryOp) and node is not parent.elze)
      assoc_left = is_left_associative(parent)
      if (prec < parent_prec) or \
         (prec == parent_prec and (assoc_left is not is_not_last_child)):
        return True
    return False

  _CTYPE_TO_STR = {
    ct.c_bool:       "bool",
    ct.c_char:       "char",
    ct.c_wchar:      "wchar_t",
    ct.c_byte:       "char",
    ct.c_ubyte:      "unsigned char",
    ct.c_short:      "short",
    ct.c_ushort:     "unsigned short",
    ct.c_int:        "int",
    ct.c_uint:       "insigned int",

    ## mbd: on my laptop, these types are ==:
    ## ['ssize_t', 'longlong', 'long']
    ct.c_long:       "long",
    # ct.c_ssize_t:    "ssize_t",
    # ct.c_longlong:   "long long",

    ## ['size_t', 'ulong', 'ulonglong']
    ct.c_size_t:     "size_t",
    # ct.c_ulong:      "unsigned long",
    # ct.c_ulonglong:  "unsigned long long",

    ct.c_float:      "float",
    ct.c_double:     "double",
    ct.c_longdouble: "long double",
    ct.c_char_p:     "char*",
    ct.c_wchar_p:    "wchar_t*",
    ct.c_void_p:     "void*",
    None:            "void"
  }

  def _ctype_to_str(self, ctype):
    if hasattr(ctype, 'contents'):
      return "%s*" % self._ctype_to_str( ctype._type_ )
    try:
      return self._CTYPE_TO_STR[ctype]
    except KeyError:
      pass
    raise Exception("Can't convert type %s to a string." % ctype)

  # -------------------------------------------------------------------------
  # visitor methods

  def visit_FunctionDecl(self, node):
    rettype = self._ctype_to_str(node.return_type)
    params = ", ".join(map(str, node.params))
    s = ""
    if node.static:
      s += "static "
    if node.inline:
      s += "inline "
    s += "%s %s(%s)" % (rettype, node.name, params)
    if node.defn:
      s += " %s" % self._genblock(node.defn)
    return s

  def visit_UnaryOp(self, node):
    if isinstance(node.op, (Op.PostInc, Op.PostDec)):
      s = "%s%s" % (node.arg, node.op)
    else:
      s = "%s%s" % (node.op, node.arg)
    return self._parentheses(node) % s

  def visit_BinaryOp(self, node):
    if isinstance(node.op, Op.ArrayRef):
      s = "%s[%s]" % (node.left, node.right)
    else:
      s = "%s %s %s" % (node.left, node.op, node.right)
    return self._parentheses(node) % s

  def visit_AugAssign(self, node):
    return "%s %s= %s" % (node.target, node.op, node.value)

  def visit_TernaryOp(self, node):
    s = "%s ? %s : %s" % (node.cond, node.then, node.elze)
    return self._parentheses(node) % s

  def visit_Cast(self, node):
    type_str = self._ctype_to_str(node.type)
    return "(%s) %s" % (type_str, node.value)

  def visit_Constant(self, node):
    if isinstance(node.value, str):
      return "'%s'" % node.value[0]
    else:
      return str(node.value)

  def visit_SymbolRef(self, node):
    if node.type:
      ty = self._ctype_to_str(node.type)
      return "%s %s" % (ty, node.name)
    else:
      return str(node.name)

  def visit_Block(self, node):
     return self._genblock(node.body)

  def visit_Return(self, node):
    if node.value:
      return "return %s" % node.value
    else:
      return "return"

  def visit_If(self, node):
    then = self._genblock(node.then)
    if node.elze:
      elze = self._genblock(node.elze)
      return "if (%s) %s else %s" % (node.cond, then, elze)
    else:
      return "if (%s) %s" % (node.cond, then)

  def visit_While(self, node):
    body = self._genblock(node.body)
    return "while (%s) %s" % (node.cond, body)

  def visit_DoWhile(self, node):
    body = self._genblock(node.body)
    return "do %s while (%s)" % (body, node.cond)

  def visit_For(self, node):
    body = self._genblock(node.body)
    return "for (%s; %s; %s) %s" % (node.init, node.test, node.incr, body)

  def visit_FunctionCall(self, node):
    args = ", ".join(map(str, node.args))
    return "%s(%s)" % (node.func, args)

  def visit_String(self, node):
    return '"%s"' % '" "'.join(node.values)

  def visit_CFile(self, node):
    stmts = self._genblock(node.body, insert_curly_brackets=False, increase_indent=False)
    return '// <file: %s.%s>%s' % (node.name, node._ext, stmts)
