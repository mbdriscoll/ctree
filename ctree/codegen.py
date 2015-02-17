from __future__ import print_function

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

    def _genblock(self, forest, insert_curly_brackets=True,
                  increase_indent=True):
        """generate block of code adding semi colons as necessary"""
        if increase_indent:
            self._indent += 1
        body = ""
        for tree in flatten(forest):
            semicolon_opt = ";" if tree._requires_semicolon() else ""
            block = tree.codegen(self._indent)
            if block is not "":
                body += self._tab() + block + semicolon_opt + "\n"
        if increase_indent:
            self._indent -= 1
        if insert_curly_brackets:
            return "{\n%s%s}" % (body, self._tab())
        else:
            return "\n%s" % body

    def _parenthesize(self, parent, child):
        """A format string that includes parentheses if needed."""
        if self._requires_parentheses(parent, child) or \
                child._force_parentheses is True:
            return "(%s)" % child
        else:
            return "%s" % child

    def _requires_parentheses(self, parent, child):
        """True by default."""
        return True
