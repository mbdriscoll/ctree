import types
import ctypes
import _ctypes

from ctree.types import (
    register_type_recognizers,
    register_type_codegenerators,
)

register_type_recognizers({
    types.IntType:     lambda (t): ctypes.c_int,
    types.LongType:    lambda (t): ctypes.c_long,
    types.BooleanType: lambda (t): ctypes.c_bool,
    types.FloatType:   lambda (t): ctypes.c_double,
    types.NoneType:    lambda (t): ctypes.c_void_p,
    types.StringType:  lambda (t): ctypes.c_char if len(t) == 1 else ctypes.c_char_p,
})

register_type_codegenerators({
    ctypes.c_int:    lambda(t): "long", # python ints are longs
    ctypes.c_long:   lambda(t): "long",
    ctypes.c_double: lambda(t): "double",
    ctypes.c_char:   lambda(t): "char",
    ctypes.c_char_p: lambda(t): "char*",
    ctypes.c_void_p: lambda(t): "void*",
    ctypes.c_bool:   lambda(t): "bool",
})
