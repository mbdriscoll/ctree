import types
import ctypes
import _ctypes
import sys

from ctree.types import (
    codegen_type,
    register_type_recognizers,
    register_type_codegenerators,
)

#Py2 and Py3 common types

register_type_recognizers(
    {
        int: ctypes.c_long,
        bool: ctypes.c_bool,
        float: ctypes.c_double,
        str: lambda t: ctypes.c_char(t.encode()) if len(t) == 1 else ctypes.c_char_p(t.encode()),
        type(None): lambda t: None
    }
)

register_type_codegenerators({
    ctypes.c_int: lambda t: "int",
    ctypes.c_long: lambda t: "long",
    ctypes.c_float: lambda t: "float",
    ctypes.c_double: lambda t: "double",
    ctypes.c_char: lambda t: "char",
    ctypes.c_char_p: lambda t: "char*",
    ctypes.c_void_p: lambda t: "void*",
    ctypes.c_bool: lambda t: "bool",
    ctypes.c_ulong: lambda t: "size_t",
    type(None): lambda n: "void",

    _ctypes.Array: lambda ct: "%s*" % codegen_type(ct._type_()),
    _ctypes._Pointer: lambda ct: "%s*" % codegen_type(ct._type_()),

})

#register version specific nodes

if sys.version_info >= (3, 0):
    pass

else:

    register_type_recognizers({
        long: ctypes.c_long
    })
