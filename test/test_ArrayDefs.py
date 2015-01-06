import ctypes as ct

from util import CtreeTest
from ctree.c.nodes import SymbolRef, Constant, Add, Mul, ArrayDef, Sub


class TestArrayDefs(CtreeTest):

    def test_simple_array_def(self):
        self._check_code(ArrayDef(
            SymbolRef('hi', ct.c_int()), Constant(2),
            [Constant(0), Constant(1)]
        ), "int hi[2] = { 0, 1 }")

    def test_complex(self):
        node = ArrayDef(
            SymbolRef('myArray', ct.c_int()),
            Constant(2),
            [
                Add(SymbolRef('b'), SymbolRef('c')),
                Mul(Sub(Constant(99), SymbolRef('d')), Constant(200))
            ]
        )
        self._check_code(node, "int myArray[2] = { b + c, (99 - d) * 200 }")
