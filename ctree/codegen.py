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
    body = ""
    for tree in forest:
      sc = ";" if tree._requires_semicolon() else ""
      body += self._tab() + tree.codegen(self._indent) + sc + "\n"
    self._indent -= 1
    return "{\n%s%s}" % (body, self._tab())

  def _parentheses(self, node):
    """A format string that includes parentheses if needed."""
    return "(%s)" if self._requires_parentheses(node) else "%s"

  def _requires_parentheses(self, node):
    return True

