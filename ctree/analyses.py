from ctree.visitors import NodeVisitor
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


class VerifyOnlyCAstNodes(NodeVisitor):
  """
  Checks that every node in the tree is an instance of
  ctree.nodes.c.CAstNode. Raises an exception if a bad node
  is found.
  """
  def visit(self, node):
    if not isinstance(node, CAstNode):
      raise AstValidationError("Expected a pure C ast, but found a non-CAstNode: %s." % node)
    self.generic_visit(node)
