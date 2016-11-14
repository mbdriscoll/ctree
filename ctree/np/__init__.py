import numpy as np
import ctypes as ct

from ctree.types import (
    codegen_type,
    register_type_recognizers,
    register_type_codegenerators,
)

def codegen_ndptr(ndptr):
    prefix = ""
    if getattr(ndptr, "_global", False):
        prefix += "__global "
    return prefix + "%s*" % codegen_type(ndptr._dtype_.type())

register_type_recognizers({
    np.ndarray: lambda obj: np.ctypeslib.as_ctypes(obj),
    np.bool8:            ct.c_bool,

    # signed integer types
    np.byte:             ct.c_char,
    np.short:            ct.c_short,
    np.intc:             ct.c_int,
    np.longlong:         ct.c_longlong,

    # technically not universally compatible
    np.int8:             ct.c_char,
    np.int16:            ct.c_short,
    np.int32:            ct.c_int,
    np.int64:            ct.c_long,

    # unsigned integer types
    np.ubyte:            ct.c_ubyte,
    np.ushort:           ct.c_ushort,
    np.uintc:            ct.c_uint,
    np.ulonglong:        ct.c_ulonglong,

    # floating point types
    np.single:           ct.c_float,
    np.float32:          ct.c_float,
    np.double:           ct.c_double,
    np.float64:          ct.c_double,
})

register_type_codegenerators({
    # pointers
    np.ctypeslib._ndptr: codegen_ndptr,

    # boolean types
    np.bool8:            lambda t: "bool",

    # signed integer types
    np.byte:             lambda t: "char",
    np.short:            lambda t: "short",
    np.intc:             lambda t: "int",
    np.longlong:         lambda t: "long long",

    # technically not universally compatible
    np.int8:             lambda t: "char",
    np.int16:            lambda t: "short",
    np.int32:            lambda t: "int",
    np.int64:            lambda t: "long",

    # unsigned integer types
    np.ubyte:            lambda t: "unsigned byte",
    np.ushort:           lambda t: "unsigned short",
    np.uintc:            lambda t: "unsigned int",
    np.ulonglong:        lambda t: "unsigned long long",

    # floating point types
    np.single:           lambda t: "float",
    np.float32:          lambda t: "float",
    np.double:           lambda t: "double",
    np.float64:          lambda t: "double",
})
