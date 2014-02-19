"""
Defines the hierarchy of AST nodes.

"""

import ast
import logging


class CAstNode(ast.AST):
  """Base class for all AST nodes in ctree."""
  _fields = []

  def __init__(self, parent=None):
    """Initialize a new AST Node."""
    super().__init__()
    self.parent = parent

  def __setattr__(self, name, value):
    """Set attribute and preserve parent pointers."""
    if name != "parent":
      if isinstance(value, CAstNode):
        value.parent = self
      elif isinstance(value, list):
        for grandchild in value:
          if isinstance(grandchild, CAstNode):
            grandchild.parent = self
    super().__setattr__(name, value)

  def __str__(self):
    from ctree.codegen import CodeGenerator
    return CodeGenerator().visit(self)


class Statement(CAstNode):
  """Section B.2.3 6.6."""
  pass


class Expression(CAstNode):
  """Cite me."""
  pass


class JumpStatement(Statement):
  """Section B.2.3 6.6.6."""
  pass


class ReturnStatement(Statement):
  """Section B.2.3 6.6.6 line 4."""
  _fields = ['value']
  def __init__(self, value=None):
    self.value = value


class Token(CAstNode):
  """Section B.1.1 6.1."""
  pass


class Constant(Token):
  """Section B.1.4 6.1.3."""
  _attrs = ['value']
  def __init__(self, value):
    self.value = value


class BinaryOp(Expression):
  """Cite me."""
  _fields = ['left', 'right']
  _attrs = ['op']
  def __init__(self, left, op, right):
    self.left = left
    self.op = op
    self.right = right


class UnaryOp(Expression):
  """Cite me."""
  _fields = ['arg']
  _attrs = ['op']
  def __init__(self, op, arg):
    self.op = op
    self.arg = arg

class SymbolRef(Expression):
  """Cite me."""
  _attrs = ['name']
  def __init__(self, name):
    self.name = name


class FunctionDecl(Statement):
  """Cite me."""
  _fields = ['return_type', 'name', 'params', 'defn']
  def __init__(self, return_type, name, params, defn=None):
    self.return_type = return_type
    self.name = name
    self.type = type
    self.defn = defn


class Type(CAstNode):
  """Cite me."""
  pass


class Void(Type):   pass
class Char(Type):   pass
class Int(Type):    pass
class Float(Type):  pass
class Long(Type):   pass
class Double(Type): pass

class Ptr(Type):
  """Cite me."""
  _fields = ['base']
  def __init__(self, base):
    self.base = base

class FuncType(Type):
  """Cite me."""
  _fields = ['return_type', 'arg_types']
  def __init__(self, return_type, arg_types=[]):
    self.return_type = return_type
    self.arg_types = arg_types


class Operator(object):
  """Cite me."""
  pass

class Add(Operator): pass
class Sub(Operator): pass
class Mul(Operator): pass
class Div(Operator): pass
class Mod(Operator): pass
class Gt(Operator): pass
class Lt(Operator): pass
class GtE(Operator): pass
class LtE(Operator): pass
class Eq(Operator): pass
class NotEq(Operator): pass
class BitAnd(Operator): pass
class BitOr(Operator): pass
class BitShL(Operator): pass
class BitShR(Operator): pass
class BitXor(Operator): pass
class BitNot(Operator): pass
class And(Operator): pass
class Or(Operator): pass
class Xor(Operator): pass
class Not(Operator): pass
class Inc(Operator): pass
class Dec(Operator): pass
class Ref(Operator): pass
class Deref(Operator): pass
