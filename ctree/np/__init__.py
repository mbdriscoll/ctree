import numpy as np

from ctree.types import (
    codegen_type,
    register_type_recognizers,
    register_type_codegenerators,
)

register_type_recognizers({
    np.ndarray: lambda obj: np.ctypeslib.as_ctypes(obj)
})

register_type_codegenerators({
    # pointers
    np.ctypeslib._ndptr: lambda t: "%s*" % codegen_type(t._dtype_.type()),

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
