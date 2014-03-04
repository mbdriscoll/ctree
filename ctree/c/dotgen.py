"""
DOT generator for C constructs.
"""

from ctree.dotgen import DotGenVisitor

class CDotGen(DotGenVisitor):
  """
  Manages generation of DOT.
  """
  def label_SymbolRef(self, node):
    s = r"name: %s" % node.name
    #if node.type:
    #  s += r"\ntype: %s" % node.type
    if node.ctype:
      s += r"\nctype: %s" % node.ctype
    return s

  def label_FunctionDecl(self, node):
    s = r"name: %s\nreturn_type: %s" % (node.name, node.return_type)
    if node.static:
      s += r"\nstatic"
    if node.inline:
      s += r"\ninline"
    if node.kernel:
      s += r"\n__kernel"
    return s

  def label_Constant(self, node):
    return "value: %s" % node.value

  def label_String(self, node):
    return r'values: \"%s\"' % r'\" \"'.join(node.values)

  def label_CFile(self, node):
    return "name: %s" % node.name
