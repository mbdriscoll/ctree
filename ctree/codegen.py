"""
base class for generating code appropriate to the selected backend
"""
from ctree.visitors import NodeVisitor
from ctree.util import flatten

class CodeGenVisitor(NodeVisitor):
    """
    Return a string containing the program text.
    """

    def __init__(self, indent=0):
        self._indent = indent

    # -------------------------------------------------------------------------
    # common support methods

    def _tab(self):
        """return correct spaces if tab found"""
        return "    " * self._indent

    def _genblock(self, forest, insert_curly_brackets=True, increase_indent=True):
        """generate block of code adding semi colons as necessary"""
        if increase_indent:
            self._indent += 1
        body = ""
        for tree in flatten(forest):
            semicolon_opt = ";" if tree._requires_semicolon() else ""
            body += self._tab() + tree.codegen(self._indent) + semicolon_opt + "\n"
        if increase_indent:
            self._indent -= 1
        if insert_curly_brackets:
            return "{\n%s%s}" % (body, self._tab())
        else:
            return "\n%s" % body

    def _parentheses(self, node):
        """A format string that includes parentheses if needed."""
        return "(%s)" if self._requires_parentheses(node) else "%s"

    def _requires_parentheses(self, _):
        """TODO: figure out why this is always true"""
        return True
