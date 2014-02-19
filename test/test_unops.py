import unittest

from ctree.nodes import *

class TestUnaryOps(unittest.TestCase):

  def setUp(self):
    self.foo = SymbolRef("foo")

  def test_plus(self):
    binop = UnaryOp(Add(), self.foo)
    assert str(binop) == "+foo"

  def test_minus(self):
    binop = UnaryOp(Sub(), self.foo)
    assert str(binop) == "-foo"

  def test_bitnot(self):
    binop = UnaryOp(BitNot(), self.foo)
    assert str(binop) == "~foo"

  def test_not(self):
    binop = UnaryOp(Not(), self.foo)
    assert str(binop) == "!foo"

  def test_ref(self):
    binop = UnaryOp(Ref(), self.foo)
    assert str(binop) == "&foo"

  def test_deref(self):
    binop = UnaryOp(Deref(), self.foo)
    assert str(binop) == "*foo"
