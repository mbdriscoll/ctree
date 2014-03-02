"""
DOT generator for C constructs.
"""

from ctree.dotgen import DotGenVisitor

class CDotGen(DotGenVisitor):
  """
  Manages generation of DOT.
  """
  def label_SymbolRef(self, node):
    s = "name: %s" % node.name
    if node.type:
      s += "\ntype: %s" % node.type.__name__
    if node.ctype:
      s += "\nctype: %s" % node.ctype
    return s

  def label_FunctionDecl(self, node):
    return "name: %s\nreturn_type: %s" % \
      (node.name, node.return_type)

  def label_Constant(self, node):
    return "value: %s" % node.value

  def label_String(self, node):
    return "value: %s" % node.value
