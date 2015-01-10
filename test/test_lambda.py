import unittest
import ctypes as ct
import ast
import sys

from ctree.transformations import PyBasicConversions, DeclarationFiller
from ctree.c.nodes import *


class TestAssigns(unittest.TestCase):


    def mini_transform(self, node):
        """
        This method acts as a simulation of a specializer's transform() method. It's the bare minimum required of
        a transform() method by the specializer writer.

        :param node: the node to transform
        :return: the node transformed through PyBasicConversions into a rough C-AST.
        """
        transformed_node = PyBasicConversions().visit(node)

        transformed_node.name = "apply"
        transformed_node.return_type = ct.c_int32()

        for param in transformed_node.params:
            param.type = ct.c_int32()

        return transformed_node

    def mini__call__(self, node):
        """
        This method acts as a simulation of jit.py's __call__() method. The specializer writer does not have to write
        this method.

        :param node: the node to generate code for
        :return: a type-complete C-AST corresponding to the input node
        """
        transformed_node = self.mini_transform(node)
        return DeclarationFiller().visit(transformed_node)

    @unittest.skipIf(sys.version_info >= (3,0), 'Lambdas changed in py3k')
    def test_one_arg_lambda(self):
        """
        This method tests the squaring lambda function, a one argument lambda function.
        """
        square_lambda_node = ast.Lambda(args = ast.arguments([SymbolRef("x")], None, None, None), body = Mul(SymbolRef("x"), SymbolRef("x")))

        # simulating __call__()
        type_inferred_node = self.mini__call__(square_lambda_node)

        self.assertEqual(str(type_inferred_node), "int apply(int x) {\n" + \
                                                "    return x * x;\n}")


    @unittest.skipIf(sys.version_info >= (3,0), 'Lambdas changed in py3k')
    def test_two_arg_lambda(self):
        """
        This method tests the adding lambda function, a two argument lambda function.
        """
        add_lambda_node = ast.Lambda(args = ast.arguments([SymbolRef("x"), SymbolRef("y")], None, None, None), body = Add(SymbolRef("x"), SymbolRef("y")))

        # simulating __call__()
        type_inferred_node = self.mini__call__(add_lambda_node)

        self.assertEqual(str(type_inferred_node), "int apply(int x, int y) {\n" + \
                                                "    return x + y;\n}")
