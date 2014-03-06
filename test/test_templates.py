import unittest
from textwrap import dedent

from ctree.templates.nodes import *
from ctree.c.nodes import Constant, While


class TestStringTemplates(unittest.TestCase):
    def _check(self, tree, expected):
        actual = tree.codegen()
        self.assertEqual(actual, dedent(expected))

    def test_no_template_args(self):
        tree = StringTemplate("empty", {})
        self._check(tree, "empty")

    def test_simple_template_one(self):
        tree = StringTemplate("return $one", {'one': Constant(1)})
        self._check(tree, "return 1")

    def test_simple_template_two(self):
        tree = StringTemplate("return $one $two", {
            'one': Constant(1),
            'two': Constant(2),
        })
        self._check(tree, "return 1 2")

    def test_dotgen(self):
        tree = StringTemplate("return $one $two", {
            'one': Constant(1),
            'two': Constant(2),
        })
        from ctree.dotgen import to_dot
        dot = to_dot(tree)

    def test_indent_0(self):
        d = {'cond': Constant(1)}
        t = """\
        while($cond)
            printf("hello");
        """
        tree = While(Constant(0), [StringTemplate(t, d)])
        self._check(tree, """\
        while (0) {
            while(1)
                printf("hello");
        }""")

    def test_indent_1(self):
        d = {'cond': Constant(1)}
        t = """\
        while($cond)
            printf("hello");
        """
        tree = StringTemplate(t, d)
        self._check(tree, """\
        while(1)
            printf("hello");""")
