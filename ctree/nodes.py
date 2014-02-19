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

class FunctionCall(Expression):
  """Cite me."""
  _fields = ['func', 'args']
  def __init__(self, func, args=[]):
    self.func = func
    self.args = args

class Token(CAstNode):
  """Section B.1.1 6.1."""
  pass


class Constant(Token):
  """Section B.1.4 6.1.3."""
  _attrs = ['value']
  def __init__(self, value):
    self.value = value


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


class UnaryOp(Expression):
  """Cite me."""
  _fields = ['arg']
  def __init__(self, arg):
    self.arg = arg

class Plus(UnaryOp): pass
class Minus(UnaryOp): pass
class Not(UnaryOp): pass
class BitNot(UnaryOp): pass
class PreInc(UnaryOp): pass
class PreDec(UnaryOp): pass
class PostInc(UnaryOp): pass
class PostDec(UnaryOp): pass
class Ref(UnaryOp): pass
class Deref(UnaryOp): pass


class BinaryOp(Expression):
  """Cite me."""
  _fields = ['left', 'right']
  def __init__(self, left, right):
    self.left = left
    self.right = right

class Add(BinaryOp): pass
class Sub(BinaryOp): pass
class Mul(BinaryOp): pass
class Div(BinaryOp): pass
class Mod(BinaryOp): pass
class Gt(BinaryOp): pass
class Lt(BinaryOp): pass
class GtE(BinaryOp): pass
class LtE(BinaryOp): pass
class Eq(BinaryOp): pass
class NotEq(BinaryOp): pass
class BitAnd(BinaryOp): pass
class BitOr(BinaryOp): pass
class BitShL(BinaryOp): pass
class BitShR(BinaryOp): pass
class BitXor(BinaryOp): pass
class And(BinaryOp): pass
class Or(BinaryOp): pass

class TernaryOp(Expression):
  """Cite me."""
  _fields = ['cond', 'then', 'elze']
  def __init__(self, cond, then, elze):
    self.cond = cond
    self.then = then
    self.elze = elze
