import unittest

from ctree.frontend import get_ast
from fixtures.sample_asts import *


class TestDotGen(unittest.TestCase):
    """
    Run the to_dot function on the fixture ASTs. There isn't
    a good way to check if the output is a legal DOT file,
    but we can at least ensure that the routine runs without
    throwing an exception.
    """

    def test_c_identity(self):
        self.assertNotEqual(identity_ast.to_dot(), "")

    def test_c_gcd(self):
        self.assertNotEqual(gcd_ast.to_dot(), "")

    def test_c_fib(self):
        self.assertNotEqual(fib_ast.to_dot(), "")

    def test_c_l2norm(self):
        self.assertNotEqual(l2norm_ast.to_dot(), "")

    def test_py_identity(self):
        self.assertNotEqual(get_ast(identity).to_dot(), "")

    def test_py_gcd(self):
        self.assertNotEqual(get_ast(gcd).to_dot(), "")

    def test_py_fib(self):
        self.assertNotEqual(get_ast(fib).to_dot(), "")
