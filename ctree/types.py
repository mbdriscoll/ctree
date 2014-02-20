from ctree.visitors import NodeVisitor
from ctree.nodes import *

class TypeFetcher(NodeVisitor):
  """
  Dynamicall computes the type of the Expression.
  """
  def visit_String(self, node):
    return Ptr(Char())

  def visit_Constant(self, node):
    n = node.value
    if isinstance(n, str):
      return Char()
    elif isinstance(n, int):
      # TODO: handle long, unsigned, etc.
      return Int()
    elif isinstance(n, float):
      # TODO: handle double
      return Float()
    else:
      raise Exception("Cannot determine type for Constant of type %s." % \
                      type(n).__class__)
