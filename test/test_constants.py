import unittest

from ctree.nodes import Constant

class TestConstants(unittest.TestCase):
  """Check that all constants convert properly."""
  def test_float_00(self): assert str(Constant(0)) == "0"
  def test_float_01(self): assert str(Constant(1)) == "1"
  def test_float_02(self): assert str(Constant(1.2)) == "1.2"

  def test_int_00(self): assert str(Constant(0)) == "0"
  def test_int_01(self): assert str(Constant(1)) == "1"
  def test_int_02(self): assert str(Constant(12)) == "12"

  def test_char_00(self): assert str(Constant("a")) == "'a'"
  def test_char_01(self): assert str(Constant("A")) == "'A'"
  def test_char_02(self): assert str(Constant("!")) == "'!'"
