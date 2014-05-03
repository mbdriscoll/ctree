"""
DOT generation for C preprocessor directives.
"""

from ctree.dotgen import DotGenLabeller


class CppDotLabeller(DotGenLabeller):
    """
    Visitor to generator DOT.
    """

    def visit_CppInclude(self, node):
        if node.angled_brackets:
            return "target: <%s>" % node.target
        else:
            return 'target: "%s"' % node.target

    def visit_CppComment(self, node):
        return "// " + node.text.replace('"', r"\"")
