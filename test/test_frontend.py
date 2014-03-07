import ast
import unittest

from ctree.frontend import get_ast
from fixtures.sample_asts import *


class TestFrontend(unittest.TestCase):
    def test_identity(self):
        self.assertIsInstance(get_ast(identity), ast.AST)

    def test_gcd(self):
        self.assertIsInstance(get_ast(gcd), ast.AST)

    def test_fib(self):
        self.assertIsInstance(get_ast(fib), ast.AST)
