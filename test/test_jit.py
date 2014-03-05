import unittest

from ctree.jit import *
from fixtures import *


class TestJit(unittest.TestCase):
    def test_identity(self):
        mod = JitModule()
        submod = CFile("generated", [identity_ast]). \
            _compile(identity_ast.codegen(), mod.compilation_dir)
        mod._link_in(submod)
        c_identity_fn = mod.get_callable(identity_ast)
        self.assertEqual(identity(1), c_identity_fn(1))
        self.assertEqual(identity(12), c_identity_fn(12))
        self.assertEqual(identity(123), c_identity_fn(123))

    def test_fib(self):
        mod = JitModule()
        submod = CFile("generated", [fib_ast])._compile(fib_ast.codegen(), mod.compilation_dir)
        mod._link_in(submod)
        c_fib_fn = mod.get_callable(fib_ast)
        self.assertEqual(fib(1), c_fib_fn(1))
        self.assertEqual(fib(6), c_fib_fn(6))

    def test_gcd(self):
        mod = JitModule()
        submod = CFile("generated", [gcd_ast])._compile(gcd_ast.codegen(), mod.compilation_dir)
        mod._link_in(submod)
        c_gcd_fn = mod.get_callable(gcd_ast)
        self.assertEqual(gcd(44, 122), c_gcd_fn(44, 122))
        self.assertEqual(gcd(27, 39), c_gcd_fn(27, 39))

    def test_choose(self):
        mod = JitModule()
        submod = CFile("generated", [choose_ast]). \
            _compile(choose_ast.codegen(), mod.compilation_dir)
        mod._link_in(submod)
        c_choose_fn = mod.get_callable(choose_ast)
        self.assertEqual(choose(0.2, 44, 122), c_choose_fn(0.2, 44, 122))
        self.assertEqual(choose(0.8, 44, 122), c_choose_fn(0.8, 44, 122))
        self.assertEqual(choose(0.3, 27, 39), c_choose_fn(0.3, 27, 39))
        self.assertEqual(choose(0.7, 27, 39), c_choose_fn(0.7, 27, 39))
