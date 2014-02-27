"""
OpenMP nodes supported by ctree.
"""

from ctree.nodes.common import CtreeNode
from ctree.visitors import NodeVisitor
from ctree.codegen import CodeGenVisitor
from ctree.dotgen import DotGenVisitor

# ---------------------------------------------------------------------------
# openmp nodes

class OmpNode(CtreeNode):
  """Base class for all OpenMP nodes supported by ctree."""
  def codegen(self, indent=0):
    return OmpCodeGen(indent).visit(self)

  def dotgen(self, indent=0):
    return OmpDotGen().visit(self)


class OmpParallel(OmpNode):
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


# ---------------------------------------------------------------------------
# code generator

class OmpCodeGen(CodeGenVisitor):
  """
  Visitor to generate omp code.
  """
  def visit_OmpParallel(self, node):
    return "#pragma omp parallel"


# ---------------------------------------------------------------------------
# DOT generator

class OmpDotGen(DotGenVisitor):
  """
  Visitor to generator DOT.
  """
  pass
