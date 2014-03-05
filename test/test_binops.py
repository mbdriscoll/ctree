import unittest

from ctree.c.nodes import *


class TestBinaryOps(unittest.TestCase):
    def setUp(self):
        self.foo, self.bar = SymbolRef('foo'), SymbolRef('bar')

    def _check(self, op_cls, expected_string):
        node = op_cls(self.foo, self.bar)
        self.assertEqual(str(node), expected_string)

    def test_add(self):
        self._check(Add, "foo + bar")

    def test_sub(self):
        self._check(Sub, "foo - bar")

    def test_mul(self):
        self._check(Mul, "foo * bar")

    def test_div(self):
        self._check(Div, "foo / bar")

    def test_mod(self):
        self._check(Mod, "foo % bar")

    def test_gt(self):
        self._check(Gt, "foo > bar")

    def test_gte(self):
        self._check(GtE, "foo >= bar")

    def test_lt(self):
        self._check(Lt, "foo < bar")

    def test_lte(self):
        self._check(LtE, "foo <= bar")

    def test_eq(self):
        self._check(Eq, "foo == bar")

    def test_neq(self):
        self._check(NotEq, "foo != bar")

    def test_and(self):
        self._check(And, "foo && bar")

    def test_or(self):
        self._check(Or, "foo || bar")

    def test_bitxor(self):
        self._check(BitXor, "foo ^ bar")

    def test_bitand(self):
        self._check(BitAnd, "foo & bar")

    def test_bitor(self):
        self._check(BitOr, "foo | bar")

    def test_bitshl(self):
        self._check(BitShL, "foo << bar")

    def test_bitshr(self):
        self._check(BitShR, "foo >> bar")

    def test_comma(self):
        self._check(Comma, "foo , bar")

    def test_dot(self):
        self._check(Dot, "foo . bar")

    def test_arrow(self):
        self._check(Arrow, "foo -> bar")


class TestArrayRefs(unittest.TestCase):
    def _check(self, tree, expected):
        actual = str(tree)
        self.assertEqual(actual, expected)

    def test_arrayref_00(self):
        foo, bar = SymbolRef('foo'), SymbolRef('bar')
        tree = ArrayRef(foo, bar)
        self._check(tree, "foo[bar]")
