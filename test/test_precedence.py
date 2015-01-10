import unittest
import ctypes as ct

from ctree.c.nodes import *
from ctree.precedence import *


class TestPrecedence(unittest.TestCase):
    def setUp(self):
        self.args = (SymbolRef('a'), SymbolRef('b'), SymbolRef('c'))

    def _check(self, tree, expected):
        actual = str(tree)
        self.assertEqual(actual, expected)

    def test_addmul_rhs(self):
        a, b, c = self.args
        tree = Add(a, Mul(b, c))
        self._check(tree, "a + b * c")

    def test_addmul_lhs(self):
        a, b, c = self.args
        tree = Add(Mul(a, b), c)
        self._check(tree, "a * b + c")

    def test_muladd_rhs(self):
        a, b, c = self.args
        tree = Mul(a, Add(b, c))
        self._check(tree, "a * (b + c)")

    def test_muladd_lhs(self):
        a, b, c = self.args
        tree = Mul(Add(a, b), c)
        self._check(tree, "(a + b) * c")

    def test_muladd_lhs_rhs(self):
        a, b, c = self.args
        tree = Mul(Add(a, b), Add(c, a))
        self._check(tree, "(a + b) * (c + a)")

    def test_muladd_nested(self):
        a, b, c = self.args
        tree = Add(a, Mul(b, Add(c, a)))
        self._check(tree, "a + b * (c + a)")

    def test_preinc_muladd(self):
        a, b, c = self.args
        tree = Mul(PreInc(Add(a, b)), c)
        self._check(tree, "++ (a + b) * c")

    def test_not_and_or(self):
        a, b, c = self.args
        tree = Not(Or(And(a, b), c))
        self._check(tree, "! (a && b || c)")

    def test_sub_postinc(self):
        a, b, c = self.args
        tree = Sub(Sub(PostInc(a)), b)
        self._check(tree, "- a ++ - b")

    def test_sub_unary_binary(self):
        a, b, c = self.args
        tree = Sub(Sub(a, b))
        self._check(tree, "- (a - b)")

    def test_sub_add_unary_binary(self):
        a, b, c = self.args
        tree = Add(Sub(Sub(a, Add(b))), c)
        self._check(tree, "- (a - + b) + c")

    def test_postinc_unary(self):
        a, b, c = self.args
        tree = PostInc(Sub(a))
        self._check(tree, "(- a) ++")

    def test_cast1(self):
        a, b, c = self.args
        tree = Add(Cast(ct.c_int(), a), b)
        self._check(tree, "(int) a + b")

    def test_cast2(self):
        a, b, c = self.args
        tree = Cast(ct.c_int(), Add(a, b))
        self._check(tree, "(int) (a + b)")


class TestAssociativityPrecedence(unittest.TestCase):
    """
    Tests insertion of parentheses for trees of operators that
    have the same precedence, and therefore we need to consider
    their associativity.
    """

    def setUp(self):
        self.args = (SymbolRef('a'), SymbolRef('b'), SymbolRef('c'))

    def _check(self, tree, expected):
        actual = str(tree)
        self.assertEqual(actual, expected)

    def test_subadd_rhs(self):
        a, b, c = self.args
        tree = Sub(a, Add(b, c))
        self._check(tree, "a - (b + c)")

    def test_subadd_lhs(self):
        a, b, c = self.args
        tree = Sub(Add(a, b), c)
        self._check(tree, "a + b - c")

    def test_complicated_00(self):
        a, b, c = self.args
        tree = Sub(Add(a, Sub(b, a)), Add(Sub(a, b), c))
        self._check(tree, "a + (b - a) - (a - b + c)")

    def test_augassign(self):
        a, b, c = self.args
        tree = AddAssign(a, AddAssign(b, c))
        self._check(tree, "a += b += c")

    def test_ternary_cond(self):
        a, b, c = self.args
        cond = TernaryOp(a, b, c)
        tree = TernaryOp(cond, c, b)
        self._check(tree, "(a ? b : c) ? c : b")

    def test_ternary_then(self):
        a, b, c = self.args
        then = TernaryOp(a, b, c)
        tree = TernaryOp(c, then, a)
        self._check(tree, "c ? (a ? b : c) : a")

    def test_ternary_else(self):
        a, b, c = self.args
        elze = TernaryOp(a, b, c)
        tree = TernaryOp(c, b, elze)
        self._check(tree, "c ? b : a ? b : c")

    def test_bad_precedence_arg(self):
        with self.assertRaises(Exception):
            get_precedence(Constant(2.3))

    def test_bad_op(self):
        a, b, c = self.args
        tree = BinaryOp(a, b, c)
        with self.assertRaises(Exception):
            get_precedence(tree)

    def test_bad_associativity_arg(self):
        with self.assertRaises(Exception):
            is_left_associative(Constant(2.3))
