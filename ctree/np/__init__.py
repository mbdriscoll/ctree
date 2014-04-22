import numpy as np

from ctree.types import (
    register_type_recognizers,
)

register_type_recognizers({
    np.ndarray: lambda obj: np.ctypeslib.as_ctypes(obj)
})
