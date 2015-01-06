import unittest
import ast

from ctree.transformations import PyBasicConversions
from ctree.c.nodes import *


class TestAssigns(unittest.TestCase):
    def setUp(self):
        self.foo, self.bar = SymbolRef("foo"), SymbolRef("bar")

    def test_simple_assign(self):
        node = Assign(self.foo, self.bar)
        self.assertEqual(str(node), "foo = bar")


    def test_multiple_assign_simple(self):
        node = ast.Assign([ast.Tuple(elts = (ast.Name(id = "x", ctx = None), ast.Name(id = "y", ctx = None)))], ast.Tuple(elts = (ast.Name(id = "x", ctx = None), ast.Name(id = "y", ctx = None))))
        transformed_node = PyBasicConversions().visit(node)

        self.assertEqual(str(transformed_node), "\n____temp__x = x;\n____temp__y = y;\nx = ____temp__x;\ny = ____temp__y;\n")

    def test_multiple_assign_constant(self):
        node = ast.Assign([ast.Tuple(elts = (ast.Name(id = "x", ctx = None), ast.Name(id = "y", ctx = None)))], ast.Tuple(elts = (Constant(1), Constant(2))))
        transformed_node = PyBasicConversions().visit(node)

        self.assertEqual(str(transformed_node), "\nx = 1;\ny = 2;\n")

    def test_multiple_assign_dependent(self):
        node = ast.Assign([ast.Tuple(elts = (ast.Name(id = "x", ctx = None), ast.Name(id = "y", ctx = None)))], ast.Tuple(elts = (ast.Name(id = "y", ctx = None), ast.Name(id = "x", ctx = None))))
        transformed_node = PyBasicConversions().visit(node)

        self.assertEqual(str(transformed_node), "\n____temp__x = x;\n____temp__y = y;\ny = ____temp__y;\nx = ____temp__x;\n")

    def test_multiple_assign_dependent(self):
        node = ast.Assign([ast.Tuple(elts = (ast.Name(id = "x", ctx = None), ast.Name(id = "y", ctx = None)))], ast.Tuple(elts = (FunctionCall(func = 'square', args = [Constant(5), Constant(5)]), FunctionCall(func = 'square', args = [Constant(5), Constant(5)]))))
        transformed_node = PyBasicConversions().visit(node)

        self.assertEqual(str(transformed_node), "\n____temp__x = square(5, 5);\n____temp__y = square(5, 5);\nx = ____temp__x;\ny = ____temp__y;\n")
