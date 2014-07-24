"""
Support for Python ast nodes in the 'ast' module.
"""

import ast

# ---------------------------------------------------------------------------
# dot generator

from ctree.dotgen import DotGenLabeller


class PyDotLabeller(DotGenLabeller):
    """
    Manages generation of DOT.
    """

    def visit_arg(self, node):
        s = "name: %s" % node.arg
        if node.annotation and not isinstance(node.annotation, ast.AST):
            s += "\nannotation: %s" % self._qualified_name(node.annotation)
        return s

    def visit_FunctionDef(self, node):
        return "name: %s" % node.name

    def visit_Num(self, node):
        return "n: %s" % node.n

    def visit_Name(self, node):
        return "id: %s" % node.id

    def visit_Attribute(self, node):
        return "attr: %s" % node.attr

    def visit_Str(self, node):
        return "str: %s" % node.s
