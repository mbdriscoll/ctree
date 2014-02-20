import unittest

from ctree.nodes import *

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
    self._check(tree, "++(a + b) * c")

  def test_not_and_or(self):
    a, b, c = self.args
    tree = Not(Or(And(a, b), c))
    self._check(tree, "!(a && b || c)")

  def test_sub_postinc(self):
    a, b, c = self.args
    tree = Sub(Sub(PostInc(a)), b)
    self._check(tree, "-a++ - b")

  def test_sub_unary_binary(self):
    a, b, c = self.args
    tree = Sub(Sub(a, b))
    self._check(tree, "-(a - b)")

  def test_sub_add_unary_binary(self):
    a, b, c = self.args
    tree = Add(Sub(Sub(a, Add(b))), c)
    self._check(tree, "-(a - +b) + c")

  def test_postinc_unary(self):
    a, b, c = self.args
    tree = PostInc(Sub(a))
    self._check(tree, "(-a)++")