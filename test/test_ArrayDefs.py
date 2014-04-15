import unittest

from ctree.c.nodes import *


class TestArrayDefs(unittest.TestCase):

    def test_simple_array_def(self):
        self.assertEqual(str(ArrayDef([Constant(0), Constant(1)])), "{ 0, 1 }")

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
        self.assertEqual(str(node), "myArray = { b + c, (99 - d) * 200 }")
