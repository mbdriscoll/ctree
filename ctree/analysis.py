from ctree.visitors import NodeVisitor
from ctree.nodes import *

class Scope(object):
  
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
