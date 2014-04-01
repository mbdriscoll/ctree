import unittest

from ctree.util import *


class TestTruncate(unittest.TestCase):
    def test_no_truncate(self):
        text = 'arst'
        self.assertEqual(truncate(text), text)

    def test_trunctate(self):
        text = 'a\na\na\na\na\na\na\na\na\na\na\na \
                \na\na\na\na\na\na\na\na\na\na\na \
                \na\na\na\na\na\na\na\na\na\na'
        self.assertNotEqual(truncate(text), text)


class TestLowerCaseUnderscoreToCamelCase(unittest.TestCase):
    def test_simple(self):
        text = 'this_is_a_name'
        self.assertEqual(
            lower_case_underscore_to_camel_case(text),
            'ThisIsAName'
        )
