from ctree.visitors import NodeVisitor

class CodeGenerator(NodeVisitor):
  def visit_Float(self, node):
    return node.value
