from ctree.visitors import NodeVisitor


class CodeGenVisitor(NodeVisitor):
    """
    Return a string containing the program text.
    """

    def __init__(self, indent=0):
        self._indent = indent

    # -------------------------------------------------------------------------
    # common support methods

    def _tab(self):
        return "    " * self._indent

    def _genblock(self, forest, insert_curly_brackets=True, increase_indent=True):
        if increase_indent:
            self._indent += 1
        body = ""
        for tree in forest:
            sc = ";" if tree._requires_semicolon() else ""
            body += self._tab() + tree.codegen(self._indent) + sc + "\n"
        if increase_indent:
            self._indent -= 1
        if insert_curly_brackets:
            return "{\n%s%s}" % (body, self._tab())
        else:
            return "\n%s" % body

    def _parentheses(self, node):
        """A format string that includes parentheses if needed."""
        return "(%s)" if self._requires_parentheses(node) else "%s"

    def _requires_parentheses(self, node):
        return True

