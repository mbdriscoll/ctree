import unittest
import ctypes as ct
import ast
from ctree.transformations import PyBasicConversions, DeclarationFiller


from ctree.c.nodes import *


class TestAssigns(unittest.TestCase):
    def setUp(self):
        self.foo, self.bar = SymbolRef("foo"), SymbolRef("bar")

    def test_simple_assign(self):
        node = Assign(self.foo, self.bar)
        self.assertEqual(str(node), "foo = bar")


    def test_multiple_assign_simple1(self):
        node = ast.Assign([ast.Tuple(elts = (ast.Name(id = "x", ctx = None), ast.Name(id = "y", ctx = None)))], ast.Tuple(elts = (ast.Name(id = "x", ctx = None), ast.Name(id = "y", ctx = None))))
        transformed_node = PyBasicConversions().visit(node)

        self.assertEqual(str(transformed_node), "\n____temp__x = x;\n____temp__y = y;\ny = ____temp__y;\nx = ____temp__x;\n")

    def test_multiple_assign_simple2(self):
        node = ast.Assign([ast.Tuple(elts = (ast.Name(id = "x", ctx = None), ast.Name(id = "y", ctx = None)))], ast.Tuple(elts = (ast.Name(id = "y", ctx = None), ast.Name(id = "x", ctx = None))))
        transformed_node = PyBasicConversions().visit(node)

        self.assertEqual(str(transformed_node), "\n____temp__x = y;\n____temp__y = x;\nx = ____temp__x;\ny = ____temp__y;\n")
