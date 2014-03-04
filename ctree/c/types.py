import ctypes

from ctree.types import CtreeType, CtreeTypeResolver

class CType(CtreeType):
  """Base class for all built-in CTypes."""
  def codegen(self):
    from ctree.c.codegen import CCodeGen
    return CCodeGen().visit(self)

  def dotgen(self):
    from ctree.c.dotgen import CDotGen
    return CDotGen().visit(self)

  def as_ctype(self):
    return self._ctype

class Void(CType):   _ctype = ctypes.c_void_p
class Char(CType):   _ctype = ctypes.c_char
class Int(CType):    _ctype = ctypes.c_int
class Long(CType):   _ctype = ctypes.c_long
class Float(CType):  _ctype = ctypes.c_float
class Double(CType): _ctype = ctypes.c_double

class Ptr(CType):
  _fields = ['base_type']
  def __init__(self, base_type=Void()):
    self.base_type = base_type

class FuncType(CType):
  _fields = ['return_type', 'arg_types']
  def __init__(self, return_type=Void(), arg_types=[]):
    self.return_type = return_type
    self.arg_types = arg_types

  def as_ctype(self):
    return_ctype = self.return_type.as_ctype()
    arg_ctypes = [arg_type.as_ctype() for arg_type in self.arg_types]
    return ctypes.CFUNCTYPE(return_ctype, *arg_ctypes)

class CTypeResolver(CtreeTypeResolver):
  @staticmethod
  def resolve(obj):
    if   isinstance(obj, int):   return Int()
    elif isinstance(obj, float): return Double()
    elif isinstance(obj, str):   return Ptr(Char())
