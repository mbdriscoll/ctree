"""
C preprocessor nodes supported by ctree.
"""

from ctree.ast import CtreeNode

class CppNode(CtreeNode):
  """Base class for all C Preprocessor nodes in ctree."""
  def codegen(self, indent=0):
    from ctree.cpp.codegen import CppCodeGen
    return CppCodeGen(indent).visit(self)

  def dotgen(self, indent=0):
    from ctree.cpp.dotgen import CppDotGen
    return CppDotGen().visit(self)
