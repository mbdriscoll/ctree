import unittest

from ctree.analyses import *
from ctree.frontend import get_ast
from fixtures.sample_asts import *


class TestVerifyOnlyCtreeNodes(unittest.TestCase):
    def _check(self, tree):
        VerifyOnlyCtreeNodes().visit(tree)

    def _check_raises(self, tree):
        with self.assertRaises(AstValidationError):
            self._check(tree)

    def test_identity_py(self):
        self._check_raises(get_ast(identity))

    def test_fib_py(self):
        self._check_raises(get_ast(fib))

    def test_gcd_py(self):
        self._check_raises(get_ast(gcd))

    def test_identity_c(self):
        self._check(identity_ast)

    def test_fib_c(self):
        self._check(fib_ast)

    def test_gcd_c(self):
        self._check(gcd_ast)
