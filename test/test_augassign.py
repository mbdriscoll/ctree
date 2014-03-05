import unittest

from ctree.c.nodes import *


class TestAugAssigns(unittest.TestCase):
    def setUp(self):
        self.foo, self.bar = SymbolRef("foo"), SymbolRef("bar")

    def _check(self, node_cls, expected_string):
        node = node_cls(self.foo, self.bar)
        self.assertEqual(str(node), expected_string)

    def test_add(self):
        self._check(AddAssign, "foo += bar")

    def test_sub(self):
        self._check(SubAssign, "foo -= bar")

    def test_mul(self):
        self._check(MulAssign, "foo *= bar")

    def test_div(self):
        self._check(DivAssign, "foo /= bar")

    def test_mod(self):
        self._check(ModAssign, "foo %= bar")

    def test_bitxor(self):
        self._check(BitXorAssign, "foo ^= bar")

    def test_bitand(self):
        self._check(BitAndAssign, "foo &= bar")

    def test_bitor(self):
        self._check(BitOrAssign, "foo |= bar")

    def test_bitshl(self):
        self._check(BitShLAssign, "foo <<= bar")

    def test_bitshr(self):
        self._check(BitShRAssign, "foo >>= bar")
