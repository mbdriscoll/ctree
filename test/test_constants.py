import unittest

from ctree.c.nodes import Constant, String


class TestConstants(unittest.TestCase):
    """Check that all constants convert properly."""

    def test_float_00(self):
        assert str(Constant(0)) == "0"

    def test_float_01(self):
        assert str(Constant(1)) == "1"

    def test_float_02(self):
        assert str(Constant(1.2)) == "1.2"

    def test_int_00(self):
        assert str(Constant(0)) == "0"

    def test_int_01(self):
        assert str(Constant(1)) == "1"

    def test_int_02(self):
        assert str(Constant(12)) == "12"

    def test_char_00(self):
        assert str(Constant("a")) == "'a'"

    def test_char_01(self):
        assert str(Constant("A")) == "'A'"

    def test_char_02(self):
        assert str(Constant("!")) == "'!'"


class TestStrings(unittest.TestCase):
    """Check that strings work."""

    def test_string_full(self):
        self.assertEqual(str(String("foo")), '"foo"')

    def test_string_empty(self):
        self.assertEqual(str(String("")), '""')

    def test_string_newline(self):
        self.assertEqual(str(String(r"\n")), r'"\n"')

    def test_string_tab(self):
        self.assertEqual(str(String(r"\t")), r'"\t"')

    def test_string_multi_two(self):
        self.assertEqual(str(String("foo", "bar")), '"foo" "bar"')

    def test_string_multi_three(self):
        self.assertEqual(str(String("foo", "bar", "baz")), '"foo" "bar" "baz"')

    def test_string_none(self):
        self.assertEqual(str(String()), '""')
