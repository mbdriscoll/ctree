"""
OpenMP nodes supported by ctree.
"""
from ctree.visitors import NodeVisitor

class OmpNode(CAstNode):
  """Base class for all OpenMP nodes supported by ctree."""
  def codegen(self, indent=0):
    return OmpCodeGen(indent).visit(self)


class Parallel(OmpNode):
  """
  Represents '#pragma omp parallel' annotations.
  """
  def __init__(self, if_exp=None, private=[], first_private=[], num_threads=None, shared=[], default=None, copyin=[], reduction=[]):
    self.if_exp = if_exp
    self.private = private
    self.first_private = first_private
    self.num_threads = num_threads
    self.shared = shared
    self.default = default
    self.copyin = copyin
    self.reduction = reduction

class OmpCodeGen(CodeGenVisitor):
  """
  Visitor to generate omp code.
  """
  pass
