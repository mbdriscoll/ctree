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

    def test_template_with_transformer(self):
        from ctree.visitors import NodeTransformer
        from ctree.c.nodes import String, SymbolRef

        template = "char *str = $val"
        template_args = {
            'val': SymbolRef("hello"),
        }
        tree = StringTemplate(template, template_args)
        self._check(tree, 'char *str = hello')

        class SymbolsToStrings(NodeTransformer):
            def visit_SymbolRef(self, node):
                return String(node.name)

        tree = SymbolsToStrings().visit(tree)
        self._check(tree, 'char *str = "hello"')

    def test_template_parent_pointers(self):
        from ctree.c.nodes import SymbolRef

        symbol = SymbolRef("hello")
        template = "char *str = $val"
        template_args = {
            'val': symbol,
        }
        node = StringTemplate(template, template_args)
        self.assertIs(symbol.parent, node)

    def test_template_parent_pointers_with_transformer(self):
        from ctree.visitors import NodeTransformer
        from ctree.c.nodes import String, SymbolRef

        template = "char *str = $val"
        template_args = {
            'val': SymbolRef("hello"),
        }

        class SymbolsToStrings(NodeTransformer):
            def visit_SymbolRef(self, node):
                return String(node.name)

        tree = StringTemplate(template, template_args)
        tree = SymbolsToStrings().visit(tree)

        template_node, string = tree, tree.val
        self.assertIs(string.parent, template_node)
