import unittest

from ctree.nodes import *

class TestBinaryOps(unittest.TestCase):

  def setUp(self):
    self.one, self.two = Constant(1), Constant(2)

  def _check(self, node_cls, expected_string):
    node = node_cls(self.one, self.two)
    self.assertEqual(str(node), expected_string)

  def test_add(self):    self._check(Add, "1 + 2")
  def test_sub(self):    self._check(Sub, "1 - 2")
  def test_mul(self):    self._check(Mul, "1 * 2")
  def test_div(self):    self._check(Div, "1 / 2")
  def test_mod(self):    self._check(Mod, "1 % 2")
  def test_gt(self):     self._check(Gt,  "1 > 2")
  def test_gte(self):    self._check(GtE, "1 >= 2")
  def test_lt(self):     self._check(Lt,  "1 < 2")
  def test_lte(self):    self._check(LtE, "1 <= 2")
  def test_eq(self):     self._check(Eq,  "1 == 2")
  def test_neq(self):    self._check(NotEq, "1 != 2")
  def test_and(self):    self._check(And, "1 && 2")
  def test_or(self):     self._check(Or,  "1 || 2")
  def test_bitxor(self): self._check(BitXor, "1 ^ 2")
  def test_bitand(self): self._check(BitAnd, "1 & 2")
  def test_bitor(self):  self._check(BitOr, "1 | 2")
  def test_bitshl(self): self._check(BitShL, "1 << 2")
  def test_bitshr(self): self._check(BitShR, "1 >> 2")
  def test_comma(self):  self._check(Comma, "1 , 2")
