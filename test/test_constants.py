import unittest

from ctree.nodes import Float, Int, Char

class TestConstants(unittest.TestCase):
  """Check that all constants convert properly."""
  def test_float_00(self): assert str(Float(0)) == "0"
  def test_float_01(self): assert str(Float(1)) == "1"
  def test_float_02(self): assert str(Float(1.2)) == "1.2"

  def test_int_00(self): assert str(Int(0)) == "0"
  def test_int_01(self): assert str(Int(1)) == "1"
  def test_int_02(self): assert str(Int(12)) == "12"

  def test_char_00(self): assert str(Char("a")) == "'a'"
  def test_char_01(self): assert str(Char("A")) == "'A'"
  def test_char_02(self): assert str(Char("!")) == "'!'"
