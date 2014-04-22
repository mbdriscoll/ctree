import unittest

from util import CtreeTest
from ctree.c.nodes import *


class TestArrayDefs(CtreeTest):

    def test_simple_array_def(self):
        self._check_code(ArrayDef([Constant(0), Constant(1)]), "{ 0, 1 }")

    def test_complex(self):
        node = Assign(
            SymbolRef('myArray'),
            ArrayDef(
                [
                    Add(SymbolRef('b'), SymbolRef('c')),
                    Mul(Sub(Constant(99), SymbolRef('d')), Constant(200))
                ]
            )
        )
        self._check_code(node, "myArray = { b + c, (99 - d) * 200 }")
