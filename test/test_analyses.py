import unittest

from ctree.c.nodes import *
from ctree.analyses import *
from ctree.frontend import get_ast
from fixtures.sample_asts import *


class TestVerifyParentPointers(unittest.TestCase):
    def test_identity(self):
        VerifyParentPointers().visit(identity_ast)

    def test_fib(self):
        VerifyParentPointers().visit(fib_ast)

    def test_gcd(self):
        VerifyParentPointers().visit(gcd_ast)

    def test_raise_identity(self):
        identity_ast.find(SymbolRef, name="x").parent = None
        with self.assertRaises(AstValidationError):
            VerifyParentPointers().visit(identity_ast)

    def test_raise_fib(self):
        fib_ast.find(Constant, value=2).parent = None
        with self.assertRaises(AstValidationError):
            VerifyParentPointers().visit(fib_ast)

    def test_raise_gcd(self):
        gcd_ast.find(Return).parent = None
        with self.assertRaises(AstValidationError):
            VerifyParentPointers().visit(gcd_ast)


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
