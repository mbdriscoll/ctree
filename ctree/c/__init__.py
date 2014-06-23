import types
import ctypes
import _ctypes

from ctree.types import (
    codegen_type,
    register_type_recognizers,
    register_type_codegenerators,
)

register_type_recognizers({
    types.IntType:     lambda t: ctypes.c_long(t),
    types.LongType:    lambda t: ctypes.c_long(t),
    types.BooleanType: lambda t: ctypes.c_bool(t),
    types.FloatType:   lambda t: ctypes.c_double(t),
    types.StringType:  lambda t: ctypes.c_char(t) if len(t) == 1 else ctypes.c_char_p(t),
    types.NoneType:    lambda t: None,
})

register_type_codegenerators({
    ctypes.c_int:     lambda t: "int",
    ctypes.c_long:    lambda t: "long",
    ctypes.c_float:   lambda t: "float",
    ctypes.c_double:  lambda t: "double",
    ctypes.c_char:    lambda t: "char",
    ctypes.c_char_p:  lambda t: "char*",
    ctypes.c_void_p:  lambda t: "void*",
    ctypes.c_bool:    lambda t: "bool",
    ctypes.c_ulong:   lambda t: "size_t",
    types.NoneType:   lambda n: "void",

    _ctypes.Array:      lambda ct: "%s*" % codegen_type(ct._type_()),
    _ctypes._Pointer:   lambda ct: "%s*" % codegen_type(ct._type_()),

})
