import unittest

from ctree.nodes import *

class TestBinaryOps(unittest.TestCase):

  def setUp(self):
    self.one, self.two = Constant(1), Constant(2)

  def test_add(self):
    binop = BinaryOp(self.one, Add(), self.two)
    assert str(binop) == "1 + 2"

  def test_sub(self):
    binop = BinaryOp(self.one, Sub(), self.two)
    assert str(binop) == "1 - 2"

  def test_mul(self):
    binop = BinaryOp(self.one, Mul(), self.two)
    assert str(binop) == "1 * 2"

  def test_div(self):
    binop = BinaryOp(self.one, Div(), self.two)
    assert str(binop) == "1 / 2"

  def test_mod(self):
    binop = BinaryOp(self.one, Mod(), self.two)
    assert str(binop) == "1 % 2"

  def test_xor(self):
    binop = BinaryOp(self.one, Xor(), self.two)
    assert str(binop) == "1 ^ 2"
