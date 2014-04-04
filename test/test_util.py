import unittest

from ctree.util import truncate
from ctree.util import lower_case_underscore_to_camel_case
from ctree.util import singleton


class TestTruncate(unittest.TestCase):
    def test_no_truncate(self):
        text = 'arst'
        self.assertEqual(truncate(text), text)

    def test_trunctate(self):
        text = 'a\na\na\na\na\na\na\na\na\na\na\na \
                \na\na\na\na\na\na\na\na\na\na\na \
                \na\na\na\na\na\na\na\na\na\na'
        self.assertNotEqual(truncate(text), text)


@singleton
class Single(object):
    def id(self):
        return self.__hash__()


class TestUtil(unittest.TestCase):
    def _check(self, actual, expected):
        self.assertEqual(actual, expected)

    def test_singleton(self):
        s1 = Single
        s2 = Single

        self.assertRaises(TypeError, Single)

        self.assertEqual(s1.id, s2.id)

    def test_truncate(self):
        s = "foo"
        s_truncated = truncate(s)
        self.assertEqual(s, s_truncated)

        many_lines = "\n".join(map(lambda x: "line %d" % x, [l for l in range(500)]))
        less_lines = truncate(many_lines)

        self.assertTrue("lines suppressed" in less_lines)

    def test_lower_case_to_camel_case(self):
        s = "dog_cat"
        cc = lower_case_underscore_to_camel_case(s)

        self.assertEqual(cc,"DogCat")


class TestLowerCaseUnderscoreToCamelCase(unittest.TestCase):
    def test_simple(self):
        text = 'this_is_a_name'
        self.assertEqual(
            lower_case_underscore_to_camel_case(text),
            'ThisIsAName'
        )

