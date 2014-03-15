"""
DOT generation for C preprocessor directives.
"""

from ctree.dotgen import DotGenVisitor


class CppDotGen(DotGenVisitor):
    """
    Visitor to generator DOT.
    """

    def label_CppInclude(self, node):
        if node.angled_brackets:
            return "target: <%s>" % node.target
        else:
            return 'target: "%s"' % node.target

    def label_Comment(self, node):
        return node.text.replace('"', r"\"")
