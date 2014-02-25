import unittest

from ctree.nodes.c import *

class TestParentPointers(unittest.TestCase):

  def test_parents_unop(self):
    child = SymbolRef("foo")
    minus_op = Sub(child)
    self.assertEqual(child.parent, minus_op)

  def test_parents_binop(self):
    child0, child1 = SymbolRef("foo"), Constant(12)
    add_op = Add(child0, child1)
    self.assertEqual(child0.parent, add_op)
    self.assertEqual(child1.parent, add_op)

  def test_parents_augassign(self):
    child0, child1 = SymbolRef("foo"), Constant(12)
    add_op = AddAssign(child0, child1)
    self.assertEqual(child0.parent, add_op)
    self.assertEqual(child1.parent, add_op)

  def test_parents_while(self):
    cond, body= SymbolRef("foo"), [Constant(12), SymbolRef("bar")]
    node = While(cond, body)
    self.assertEqual(cond.parent, node)
    for child in node.body:
      self.assertEqual(child.parent, node)
