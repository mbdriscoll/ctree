import unittest

from ctree.nodes import *
from ctree.c.nodes import *
from ctree.types import get_ctree_type

from ctree.jit import LazySpecializedFunction
from ctree.jit import ConcreteSpecializedFunction

from fixtures.sample_asts import *


class TestTranslator(LazySpecializedFunction):
    def args_to_subconfig(self, args):
        return {'arg_typesig': tuple(get_ctree_type(a) for a in args)}

    def transform(self, tree, program_config):
        arg_types = program_config[0]['arg_typesig']
        func_type = FuncType(arg_types[0], list(arg_types))

        tree.set_typesig(func_type)
        proj = Project([CFile("generated", [tree])])

        return ConcreteSpecializedFunction(self.entry_point_name, proj, func_type.as_ctype())


class BadArgs(LazySpecializedFunction):
    def args_to_subconfig(self, args):
        return {'args': args}


class DefaultArgs(LazySpecializedFunction):
    def transform(self, tree, program_config):
        proj = Project([CFile("generated", [tree])])
        ctype = tree.get_type().as_ctype()
        return tree


class NoTransform(LazySpecializedFunction):
    def args_to_subconfig(self, args):
        return {'arg_typesig': tuple(get_ctree_type(arg) for arg in args)}


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

    def test_default_args_to_subconfig(self):
        c_identity = DefaultArgs(identity_ast, "identity")
        self.assertEqual(c_identity.args_to_subconfig([1, 2, 3]), {})

    def test_no_transform(self):
        c_identity = NoTransform(identity_ast, "identity")
        with self.assertRaises(NotImplementedError):
            self.assertEqual(c_identity(1.2), identity(1.2))
