from ctree.visitors import NodeTransformer
from ctree.nodes import *

class ScrubCtx(NodeVisitor):
  """
  Removes ctx attributes from Python ast.Name nodes.
  """
  def visit_Name(self, node):
    node.ctx = None
    return node


class PyLiteralsToC(NodeTransformer):
  """
  Convert numbers and strings to ctree.node.CAstNode equivalents.
  """
  def visit_Number(self, node):
    return Constant(node.n)

  def visit_Str(self, node):
    return String(node.s)
