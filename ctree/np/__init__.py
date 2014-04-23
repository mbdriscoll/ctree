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
    np.ctypeslib._ndptr: lambda t: "%s*" % codegen_type(t._dtype_.type()),
    np.float64:          lambda t: "double",
    np.float32:          lambda t: "float",
    np.int32:            lambda t: "int",
})
