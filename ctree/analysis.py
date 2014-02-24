from ctree.visitors import NodeVisitor
from ctree.nodes import *

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


class ConsistencyError(Exception):
  pass


class VerifyAllCAstNodes(NodeVisitor):
  """
  Checks that every node in the tree is an instance of
  ctree.nodes.CAstNode. Raises an exception if a bad node
  is found.
  """
  def visit(self, node):
    if not isinstance(node, CAstNode):
      raise ConsistencyError("Found a non-CAstNode of type %s." % type(node).__name__)
    self.generic_visit(node)
