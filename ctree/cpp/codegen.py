"""
Code generation for C preprocessing directives.
"""

from ctree.codegen import CodeGenVisitor

class CppCodeGen(CodeGenVisitor):
  """
  Visitor to generate C preprocessor directives.
  """
  def visit_CppInclude(self, node):
    if node.angled_brackets:
      return "#include <%s>" % node.target
    else:
      return '#include "%s"' % node.target
