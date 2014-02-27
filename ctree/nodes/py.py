"""
Support for Python ast nodes in the 'ast' module.
"""

import ast

# ---------------------------------------------------------------------------
# dot generator

from ctree.dotgen import DotGenVisitor, to_dot

class PyDotGen(DotGenVisitor):
  """
  Manages generation of DOT.
  """
  def label_arg(self, node):
    s = "name: %s" % node.arg
    if node.annotation and not isinstance(node.annotation, ast.AST):
      s += "\nannotation: %s" % self._qualified_name(node.annotation)
    return s

  def label_FunctionDef(self, node):
    return "name: %s" % node.name

  def label_Num(self, node):
    return "n: %s" % node.n

  def label_Name(self, node):
    return "id: %s" % node.id
