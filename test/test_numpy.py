import ctypes
import _ctypes

from ctree.types import (
    get_ctype,
    codegen_type,
)

from util import CtreeTest

import ctree
import ctree.c
import ctree.np
from ctree.c.nodes import SymbolRef

import numpy as np

class TestTypeRecognizer(CtreeTest):
    def test_int_array(self):
        ty = get_ctype(np.arange(10, dtype=np.int32))
        self.assertIsInstance(ty, _ctypes.Array)

class TestTypeCodeGen(CtreeTest):
    def test_int_array_1d(self):
        ty = get_ctype(np.arange(10, dtype=np.int32))
        tree = SymbolRef("i", ty)
        self._check_code(tree, "int* i")

    def test_int_array_2d(self):
        ty = get_ctype(np.arange(10, dtype=np.int32).reshape(2,5))
        tree = SymbolRef("i", ty)
        self._check_code(tree, "int** i")
