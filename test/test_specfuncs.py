import unittest

from ctree.nodes import *
from ctree.c.nodes import *
from ctree.types import get_ctree_type

from ctree.jit import LazySpecializedFunction

from fixtures import *


class TestTranslator(LazySpecializedFunction):
    def args_to_subconfig(self, args):
        return tuple([get_ctree_type(a) for a in args])

    def transform(self, tree, program_config):
        arg_types = program_config[0]
        func_type = [arg_types[0]] + list(arg_types)

        tree.set_typesig(func_type)
        tree = Project([CFile("generated", [tree])])

        return tree


class TestSpecializers(unittest.TestCase):
    def test_identity_int(self):
        c_identity = TestTranslator(identity_ast, "identity")
        self.assertEqual(c_identity(1), identity(1))

    def test_identity_float(self):
        c_identity = TestTranslator(identity_ast, "identity")
        self.assertEqual(c_identity(1.2), identity(1.2))

    def test_identity_intfloat(self):
        c_identity = TestTranslator(identity_ast, "identity")
        self.assertEqual(c_identity(1), identity(1))
        self.assertEqual(c_identity(1.2), identity(1.2))

    def test_fib_int(self):
        c_fib = TestTranslator(fib_ast, "fib")
        self.assertEqual(c_fib(1), fib(1))

    def test_fib_float(self):
        c_fib = TestTranslator(fib_ast, "fib")
        self.assertEqual(c_fib(1.2), fib(1.2))

    def test_fib_intfloat(self):
        c_fib = TestTranslator(fib_ast, "fib")
        self.assertEqual(c_fib(1), fib(1))
        self.assertEqual(c_fib(1.2), fib(1.2))

    def test_gcd_int(self):
        c_gcd = TestTranslator(gcd_ast, "gcd")
        self.assertEqual(c_gcd(1, 2), gcd(1, 2))
