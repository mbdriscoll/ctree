import unittest

from ctree.nodes import *
from ctree.c.nodes import *

from ctree.types import get_ctype
from ctypes import *

from ctree.jit import LazySpecializedFunction
from ctree.jit import ConcreteSpecializedFunction

from fixtures.sample_asts import *


class TestTranslator(LazySpecializedFunction):
    def args_to_subconfig(self, args):
        return {'arg_typesig': tuple(type(get_ctype(a)) for a in args)}

    def transform(self, tree, program_config):
        arg_types = program_config[0]['arg_typesig']
        func_type = CFUNCTYPE(arg_types[0], *arg_types)

        tree.return_type = arg_types[0]()
        for param, ty in zip(tree.params, arg_types):
            param.type = ty()

        proj = Project([CFile("generated", [tree])])

        return BasicFunction(tree.name, proj, func_type)


class BasicFunction(ConcreteSpecializedFunction):
    def __init__(self, entry, tree, typesig):
        self._c_function = self._compile(entry, tree, typesig)

    def __call__(self, *args, **kwargs):
        return self._c_function(*args, **kwargs)


class BadArgs(LazySpecializedFunction):
    def args_to_subconfig(self, args):
        return {'args': args}


class DefaultArgs(LazySpecializedFunction):
    def transform(self, tree, program_config):
        proj = Project([CFile("generated", [tree])])
        ctype = tree.get_type().as_ctype()
        return BasicFunction(tree.name, proj, ctype)


class NoTransform(LazySpecializedFunction):
    def args_to_subconfig(self, args):
        return {'arg_typesig': tuple(type(get_ctype(arg)) for arg in args)}


class TestSpecializers(unittest.TestCase):
    def test_identity_int(self):
        c_identity = TestTranslator(identity_ast)
        self.assertEqual(c_identity(1), identity(1))

    def test_identity_float(self):
        c_identity = TestTranslator(identity_ast)
        self.assertEqual(c_identity(1.2), identity(1.2))

    def test_identity_intfloat(self):
        c_identity = TestTranslator(identity_ast)
        self.assertEqual(c_identity(1), identity(1))
        self.assertEqual(c_identity(1.2), identity(1.2))

    def test_fib_int(self):
        c_fib = TestTranslator(fib_ast)
        self.assertEqual(c_fib(1), fib(1))

    def test_fib_float(self):
        c_fib = TestTranslator(fib_ast)
        self.assertEqual(c_fib(1.2), fib(1.2))

    def test_fib_intfloat(self):
        c_fib = TestTranslator(fib_ast)
        self.assertEqual(c_fib(1), fib(1))
        self.assertEqual(c_fib(1.2), fib(1.2))

    def test_gcd_int(self):
        c_gcd = TestTranslator(gcd_ast)
        self.assertEqual(c_gcd(1, 2), gcd(1, 2))

    def test_default_args_to_subconfig(self):
        c_identity = DefaultArgs(identity_ast)
        self.assertEqual(c_identity.args_to_subconfig([1, 2, 3]), {})

    def test_no_transform(self):
        c_identity = NoTransform(identity_ast)
        with self.assertRaises(NotImplementedError):
            self.assertEqual(c_identity(1.2), identity(1.2))
