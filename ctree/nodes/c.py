"""
Defines the hierarchy of AST nodes.

"""

import ast
import logging
import ctypes


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

  def to_dot(self):
    """Retrieve the AST in DOT format for vizualization."""
    from ctree.dotgen import DotGenerator
    return DotGenerator().generate_from(self)

  def get_root(self):
    """
    Traverse the parent pointer list to find the eldest
    parent without a parent, aka the root.
    """
    root = self
    while root.parent != None:
      root = root.parent
    return root

  def find_all(self, node_class, **kwargs):
    """
    Returns a generator that yields all nodes of type
    'node_class' type whose attributes match those specified
    in kwargs. For example, all FunctionDecls with name 'fib'
    can be accessed via:
    >>> my_ast.find_all(FunctionDecl, name="fib")
    """
    def pred(node):
      if type(node) == node_class:
        for attr, value in kwargs.items():
          try:
            if getattr(node, attr) != value:
              break
          except AttributeError:
            break
        else:
          return True
      return False
    return self.find_if(pred)

  def find(self, node_class, **kwargs):
    """
    Returns one node of type 'node_class' whose attributes
    match those specified in kwargs, or None if no nodes
    can be found.
    """
    matching = self.find_all(node_class, **kwargs)
    try:
      return next(matching)
    except StopIteration:
      return None

  def find_if(self, pred):
    """
    Returns all nodes satisfying the given predicate,
    or None if no satisfactory nodes are found. The search
    starts from the current node.
    """
    for node in ast.walk(self):
      if pred(node):
        yield node

  def replace(self, new_node):
    """
    Replace the current node with 'new_node'.
    """
    parent = self.parent
    assert self.parent, "Tried to replace a node without a parent."
    for fieldname, child in ast.iter_fields(parent):
      if child is self:
        setattr(parent, fieldname, new_node)
    return new_node

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
    super().__init__()


class If(Statement):
  """Cite me."""
  _fields = ['cond', 'then', 'elze']
  def __init__(self, cond=None, then=None, elze=None):
    self.cond = cond
    self.then = then
    self.elze = elze
    super().__init__()


class While(Statement):
  """Cite me."""
  _fields = ['cond', 'body']
  def __init__(self, cond=None, body=[]):
    self.cond = cond
    self.body = body
    super().__init__()


class DoWhile(Statement):
  _fields = ['body', 'cond']
  def __init__(self, body=[], cond=None):
    self.body = body
    self.cond = cond
    super().__init__()


class For(Statement):
  _fields = ['init', 'test', 'incr', 'body']
  def __init__(self, init=None, test=None, incr=None, body=None):
    self.init = init
    self.test = test
    self.incr = incr
    self.body = body
    super().__init__()


class FunctionCall(Expression):
  """Cite me."""
  _fields = ['func', 'args']
  def __init__(self, func=None, args=[]):
    self.func = func
    self.args = args
    super().__init__()


class ArrayRef(Expression):
  """Cite me."""
  _fields = ['base', 'offset']
  def __init__(self, base=None, offset=None):
    self.base = base
    self.offset = offset
    super().__init__()

class Literal(Expression):
  """Cite me."""
  pass

class Constant(Literal):
  """Section B.1.4 6.1.3."""
  def __init__(self, value=None):
    self.value = value
    super().__init__()


class Block(Statement):
  """Cite me."""
  _fields = ['body']
  def __init__(self, body=[]):
    self.body = body
    super().__init__()


class Project(CAstNode):
  """Holds a list files."""
  _fields = ['files']
  def __init__(self, files=[]):
    self.files = files
    super().__init__()


class File(CAstNode):
  """Holds a list of statements."""
  _fields = ['body']
  def __init__(self, body=[]):
    self.body = body
    super().__init__()


class String(Literal):
  """Cite me."""
  def __init__(self, value=None):
    self.value = value
    super().__init__()


class SymbolRef(Literal):
  """Cite me."""
  def __init__(self, name=None, type=None, ctype=None):
    """
    Create a new symbol with the given name. If a declaration
    type is specified, the symbol is considered a declaration
    and unparsed with the type.

    The ctype field is used when the ctype used to do Python
    type-checking differs from the type declared at the C level.
    This arises in the case of Numpy arrays where ctypes checks
    against a np.ctypeslib.ndpointer, but the C code can have
    a basic "double*" type (or something equivalent).
    """
    self.name = name
    self.type = type
    self.ctype = ctype
    super().__init__()

  def get_ctype(self):
    return self.ctype or self.type


class FunctionDecl(Statement):
  """Cite me."""
  _fields = ['params', 'defn']
  def __init__(self, return_type=None, name=None, params=None, defn=None):
    self.return_type = return_type
    self.name = name
    self.params = params
    self.defn = defn
    self.inline = False
    self.static = False
    super().__init__()

  def get_type(self):
    arg_types = [p.get_ctype() for p in self.params]
    return ctypes.CFUNCTYPE(self.return_type, *arg_types)

  def get_callable(self):
    from ctree.jit import LazyTreeBuilder
    return LazyTreeBuilder(self)

  def set_inline(self, value=True):
    self.inline = value
    return self

  def set_static(self, value=True):
    self.static = value
    return self

class UnaryOp(Expression):
  """Cite me."""
  _fields = ['arg']
  def __init__(self, op=None, arg=None):
    self.op = op
    self.arg = arg
    super().__init__()


class BinaryOp(Expression):
  """Cite me."""
  _fields = ['left', 'right']
  def __init__(self, left=None, op=None, right=None):
    self.left = left
    self.op = op
    self.right = right
    super().__init__()


class AugAssign(Expression):
  """Cite me."""
  _fields = ['target', 'value']
  def __init__(self, target=None, op=None, value=None):
    self.target = target
    self.op = op
    self.value = value
    super().__init__()


class TernaryOp(Expression):
  """Cite me."""
  _fields = ['cond', 'then', 'elze']
  def __init__(self, cond=None, then=None, elze=None):
    self.cond = cond
    self.then = then
    self.elze = elze
    super().__init__()


class Cast(Expression):
   """doc"""
   _fields = ['value']
   def __init__(self, ctype=None, value=None):
     self.type = ctype
     self.value = value
     super().__init__()


class Op:
  class _Op(object):
    def __str__(self):
      return self._c_str

  class PreInc(_Op):   _c_str = "++"
  class PreDec(_Op):   _c_str = "--"
  class PostInc(_Op):  _c_str = "++"
  class PostDec(_Op):  _c_str = "--"
  class Ref(_Op):      _c_str = "&"
  class Deref(_Op):    _c_str = "*"
  class SizeOf(_Op):   _c_str = "sizeof"
  class Add(_Op):      _c_str = "+"
  class AddUnary(_Op): _c_str = "+"
  class Sub(_Op):      _c_str = "-"
  class SubUnary(_Op): _c_str = "-"
  class Mul(_Op):      _c_str = "*"
  class Div(_Op):      _c_str = "/"
  class Mod(_Op):      _c_str = "%"
  class Gt(_Op):       _c_str = ">"
  class Lt(_Op):       _c_str = "<"
  class GtE(_Op):      _c_str = ">="
  class LtE(_Op):      _c_str = "<="
  class Eq(_Op):       _c_str = "=="
  class NotEq(_Op):    _c_str = "!="
  class BitAnd(_Op):   _c_str = "&"
  class BitOr(_Op):    _c_str = "|"
  class BitNot(_Op):   _c_str = "~"
  class BitShL(_Op):   _c_str = "<<"
  class BitShR(_Op):   _c_str = ">>"
  class BitXor(_Op):   _c_str = "^"
  class And(_Op):      _c_str = "&&"
  class Or(_Op):       _c_str = "||"
  class Not(_Op):      _c_str = "!"
  class Comma(_Op):    _c_str = ","
  class Dot(_Op):      _c_str = "."
  class Arrow(_Op):    _c_str = "->"
  class Assign(_Op):   _c_str = "="
  class ArrayRef(_Op): _c_str = "??"


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
    return UnaryOp(Op.AddUnary(), a)

def Sub(a,b=None):
  if b != None:
    return BinaryOp(a, Op.Sub(), b)
  else:
    return UnaryOp(Op.SubUnary(), a)

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
