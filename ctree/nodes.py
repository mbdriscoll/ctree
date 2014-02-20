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
  def get_type(self):
    from ctree.types import TypeFetcher
    return TypeFetcher().visit(self)


class Return(Statement):
  """Section B.2.3 6.6.6 line 4."""
  _fields = ['value']
  def __init__(self, value=None):
    self.value = value


class If(Statement):
  """Cite me."""
  _fields = ['cond', 'then', 'elze']
  def __init__(self, cond, then, elze=None):
    self.cond = cond
    self.then = then
    self.elze = elze


class While(Statement):
  """Cite me."""
  _fields = ['cond', 'body']
  def __init__(self, cond, body=[]):
    self.cond = cond
    self.body = body


class DoWhile(Statement):
  _fields = ['body', 'cond']
  def __init__(self, body, cond):
    self.body = body
    self.cond = cond


class For(Statement):
  _fields = ['init', 'test', 'incr', 'body']
  def __init__(self, init, test, incr, body):
    self.init = init
    self.test = test
    self.incr = incr
    self.body = body


class FunctionCall(Expression):
  """Cite me."""
  _fields = ['func', 'args']
  def __init__(self, func, args=[]):
    self.func = func
    self.args = args


class ArrayRef(Expression):
  """Cite me."""
  _fields = ['base', 'offset']
  def __init__(self, base, offset):
    self.base = base
    self.offset = offset


class Constant(Expression):
  """Section B.1.4 6.1.3."""
  _attrs = ['value']
  def __init__(self, value):
    self.value = value


class String(Expression):
  """Cite me."""
  _attrs = ["value"]
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
  def __init__(self, return_type, name, params=[], defn=None):
    self.return_type = return_type
    self.name = name
    self.params = params
    self.defn = defn


class Type(CAstNode):
  """Cite me."""

  def __eq__(self, other):
    """Equal if type signature is same string."""
    return str(self) == str(other)

class Void(Type):   pass
class Char(Type):   pass
class Int(Type):    pass
class UnsignedInt(Type): pass
class LongInt(Type): pass
class UnsignedLongInt(Type): pass
class Float(Type):  pass
class Long(Type):   pass
class Double(Type): pass
class LongDouble(Type): pass
class Unknown(Type): pass

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


class Param(Statement):
  """Cite me."""
  _fields = ['type', 'name']
  def __init__(self, type, name=None):
    self.type = type
    self.name = name


class UnaryOp(Expression):
  """Cite me."""
  _fields = ['arg']
  def __init__(self, op, arg):
    self.op = op
    self.arg = arg


class BinaryOp(Expression):
  """Cite me."""
  _fields = ['left', 'right']
  def __init__(self, left, op, right):
    self.left = left
    self.op = op
    self.right = right


class AugAssign(Expression):
  """Cite me."""
  _fields = ['target', 'value']
  def __init__(self, target, op, value):
    self.target = target
    self.op = op
    self.value = value


class TernaryOp(Expression):
  """Cite me."""
  _fields = ['cond', 'then', 'elze']
  def __init__(self, cond, then, elze):
    self.cond = cond
    self.then = then
    self.elze = elze


class Op:
  class _Op(object):
    def __str__(self):
      return self._c_str

    def get_precedence(self):
      # flip precedence so higher numbers mean higher precedence
      return 20 - self.precedence

    def is_left_associative(self):
      return self.left_assoc

  class _OpPrec2(_Op):
    precedence = 2
    left_assoc = True

  class _OpPrec3(_Op):
    precedence = 3
    left_assoc = False

  class _OpPrec5(_Op):
    precedence = 5
    left_assoc = True

  class _OpPrec6(_Op):
    precedence = 6
    left_assoc = True

  class _OpPrec7(_Op):
    precedence = 7
    left_assoc = True

  class _OpPrec8(_Op):
    precedence = 8
    left_assoc = True

  class _OpPrec9(_Op):
    precedence = 9
    left_assoc = True

  class _OpPrec10(_Op):
    precedence = 10
    left_assoc = True

  class _OpPrec11(_Op):
    precedence = 11
    left_assoc = True

  class _OpPrec12(_Op):
    precedence = 12
    left_assoc = True

  class _OpPrec13(_Op):
    precedence = 13
    left_assoc = True

  class _OpPrec14(_Op):
    precedence = 14
    left_assoc = True

  class _OpPrec15(_Op):
    precedence = 15
    left_assoc = False

  class _OpPrec16(_Op):
    precedence = 16
    left_assoc = False

  class _OpPrec18(_Op):
    precedence = 18
    left_assoc = True

  class PreInc(_OpPrec3):   _c_str = "++"
  class PreDec(_OpPrec3):   _c_str = "--"
  class PostInc(_OpPrec2):  _c_str = "++"
  class PostDec(_OpPrec2):  _c_str = "--"
  class Ref(_OpPrec3):      _c_str = "&"
  class Deref(_OpPrec3):    _c_str = "*"
  class SizeOf(_OpPrec3):   _c_str = "sizeof"
  class Add(_OpPrec6):      _c_str = "+"
  class Sub(_OpPrec6):      _c_str = "-"
  class Mul(_OpPrec5):      _c_str = "*"
  class Div(_OpPrec5):      _c_str = "/"
  class Mod(_OpPrec5):      _c_str = "%"
  class Gt(_OpPrec8):       _c_str = ">"
  class Lt(_OpPrec8):       _c_str = "<"
  class GtE(_OpPrec8):      _c_str = ">="
  class LtE(_OpPrec8):      _c_str = "<="
  class Eq(_OpPrec9):       _c_str = "=="
  class NotEq(_OpPrec9):    _c_str = "!="
  class BitAnd(_OpPrec10):  _c_str = "&"
  class BitOr(_OpPrec12):   _c_str = "|"
  class BitNot(_OpPrec3):   _c_str = "~"
  class BitShL(_OpPrec7):   _c_str = "<<"
  class BitShR(_OpPrec7):   _c_str = ">>"
  class BitXor(_OpPrec11):  _c_str = "^"
  class And(_OpPrec13):     _c_str = "&&"
  class Or(_OpPrec14):      _c_str = "||"
  class Not(_OpPrec3):      _c_str = "!"
  class Comma(_OpPrec18):   _c_str = ","
  class Dot(_OpPrec2):      _c_str = "."
  class Arrow(_OpPrec2):    _c_str = "->"
  class Assign(_OpPrec16):  _c_str = "="
  class Cast(_OpPrec3):     _c_str = "??"
  class ArrayRef(_OpPrec2): _c_str = "??"


# ---------------------------------------------------------------------------
# factory routines for building UnaryOps, BinaryOps, etc.

def PreInc(a):  return UnaryOp(Op.PreInc(), a)
def PreDec(a):  return UnaryOp(Op.PreDec(), a)
def PostInc(a): return UnaryOp(Op.PostInc(), a)
def PostDec(a): return UnaryOp(Op.PostDec(), a)
def BitNot(a):  return UnaryOp(Op.BitNot(), a)
def Not(a):     return UnaryOp(Op.Not(), a)
def Ref(a):     return UnaryOp(Op.Ref(), a)
def Deref(a):   return UnaryOp(Op.Deref(), a)
def SizeOf(a):  return UnaryOp(Op.SizeOf(), a)

def Add(a,b=None):
  if b != None:
    return BinaryOp(a, Op.Add(), b)
  else:
    return UnaryOp(Op.Add(), a)

def Sub(a,b=None):
  if b != None:
    return BinaryOp(a, Op.Sub(), b)
  else:
    return UnaryOp(Op.Sub(), a)

def Mul(a,b):    return BinaryOp(a, Op.Mul(), b)
def Div(a,b):    return BinaryOp(a, Op.Div(), b)
def Mod(a,b):    return BinaryOp(a, Op.Mod(), b)
def Gt(a,b):     return BinaryOp(a, Op.Gt(), b)
def Lt(a,b):     return BinaryOp(a, Op.Lt(), b)
def GtE(a,b):    return BinaryOp(a, Op.GtE(), b)
def LtE(a,b):    return BinaryOp(a, Op.LtE(), b)
def Eq(a,b):     return BinaryOp(a, Op.Eq(), b)
def NotEq(a,b):  return BinaryOp(a, Op.NotEq(), b)
def BitAnd(a,b): return BinaryOp(a, Op.BitAnd(), b)
def BitOr(a,b):  return BinaryOp(a, Op.BitOr(), b)
def BitShL(a,b): return BinaryOp(a, Op.BitShL(), b)
def BitShR(a,b): return BinaryOp(a, Op.BitShR(), b)
def BitXor(a,b): return BinaryOp(a, Op.BitXor(), b)
def And(a,b):    return BinaryOp(a, Op.And(), b)
def Or(a,b):     return BinaryOp(a, Op.Or(), b)
def Comma(a,b):  return BinaryOp(a, Op.Comma(), b)
def Dot(a,b):    return BinaryOp(a, Op.Dot(), b)
def Arrow(a,b):  return BinaryOp(a, Op.Arrow(), b)
def Assign(a,b): return BinaryOp(a, Op.Assign(), b)
def Cast(a,b):   return BinaryOp(a, Op.Cast(), b)
def ArrayRef(a,b): return BinaryOp(a, Op.ArrayRef(), b)

def AddAssign(a,b):    return AugAssign(a, Op.Add(), b)
def SubAssign(a,b):    return AugAssign(a, Op.Sub(), b)
def MulAssign(a,b):    return AugAssign(a, Op.Mul(), b)
def DivAssign(a,b):    return AugAssign(a, Op.Div(), b)
def ModAssign(a,b):    return AugAssign(a, Op.Mod(), b)
def BitXorAssign(a,b): return AugAssign(a, Op.BitXor(), b)
def BitAndAssign(a,b): return AugAssign(a, Op.BitAnd(), b)
def BitOrAssign(a,b):  return AugAssign(a, Op.BitOr(), b)
def BitShLAssign(a,b): return AugAssign(a, Op.BitShL(), b)
def BitShRAssign(a,b): return AugAssign(a, Op.BitShR(), b)
