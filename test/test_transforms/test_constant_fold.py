import unittest
import ctree.c.nodes as C
from ctree.transforms import ConstantFold


class TestConstantFold(unittest.TestCase):
    def test_add_zero(self):
        tree = C.Add(C.SymbolRef("a"), C.Constant(0))
        tree = ConstantFold().visit(tree)
        self.assertEqual(tree, C.SymbolRef("a"))

    def test_add_constants(self):
        tree = C.Add(C.Constant(20), C.Constant(10))
        tree = ConstantFold().visit(tree)
        self.assertEqual(tree, C.Constant(30))

    def test_mul_constant(self):
        tree = C.Mul(C.Constant(20), C.Constant(10))
        tree = ConstantFold().visit(tree)
        self.assertEqual(tree, C.Constant(200))

    def test_sub_constant(self):
        tree = C.Sub(C.Constant(20), C.Constant(10))
        tree = ConstantFold().visit(tree)
        self.assertEqual(tree, C.Constant(10))

    def test_div_constant(self):
        tree = C.Div(C.Constant(20), C.Constant(10))
        tree = ConstantFold().visit(tree)
        self.assertEqual(tree, C.Constant(2))

    def test_mul_by_0(self):
        tree = C.Mul(C.Constant(0), C.SymbolRef("b"))
        tree = ConstantFold().visit(tree)
        self.assertEqual(tree, C.Constant(0))

    def test_recursive_fold(self):
        tree = C.Add(C.Add(C.Constant(2), C.Constant(-2)),
                     C.SymbolRef("b"))
        tree = ConstantFold().visit(tree)
        print(tree)
        self.assertEqual(tree, C.SymbolRef("b"))
