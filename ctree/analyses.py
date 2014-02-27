from ctree.visitors import NodeVisitor
from ctree.nodes.common import *
from ctree.nodes.c import *

class DeclFinder(NodeVisitor):
  """
  Returns the first use of a particular symbol.
  """

  def find(self, node):
    assert isinstance(node, (SymbolRef)), \
      "DeclFinder only works on SymbolRefs for now."

    self.decl = None

    assert self.decl != None, \
      "Couldn't find declaration for symbol %s." % node
    return self.decl


class AstValidationError(Exception):
  pass


class VerifyOnlyCtreeNodes(NodeVisitor):
  """
  Checks that every node in the tree is an instance of
  ctree.nodes.common.CtreeNode. Raises an exception if a bad node
  is found.
  """
  def visit(self, node):
    if not isinstance(node, CtreeNode):
      raise AstValidationError("Expected a pure C ast, but found a non-CtreeNode: %s." % node)
    self.generic_visit(node)
