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

  def _genblock(self, forest):
    self._indent += 1
    body = self._tab() + \
           (";\n%s" % self._tab()).join([f.codegen(self._indent) for f in forest]) + \
           ";\n"
    self._indent -= 1
    return "{\n%s%s}" % (body, self._tab())

  def _parentheses(self, node):
    """A format string that includes parentheses if needed."""
    return "(%s)" if self._requires_parentheses(node) else "%s"

  def _requires_parentheses(self, node):
    return True

