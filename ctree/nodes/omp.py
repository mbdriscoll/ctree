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
  _fields = ['clauses']
  def __init__(self, clauses=[]):
    self.clauses = clauses


class OmpParallelFor(OmpNode):
  """ #pragma omp parallel for ... """
  _fields = ['clauses']
  def __init__(self, clauses=[]):
    self.clauses = clauses


class OmpClause(OmpNode):
  """Base class for OpenMP clauses."""
  pass


class OmpIfClause(OmpClause):
  _fields = ["exp"]
  def __init__(self, exp=None):
    self.exp = exp


class OmpNumThreadsClause(OmpClause):
  _fields = ["val"]
  def __init__(self, val=None):
    self.val = val


class OmpNoWaitClause(OmpClause):
  pass


# ---------------------------------------------------------------------------
# code generator

class OmpCodeGen(CodeGenVisitor):
  """
  Visitor to generate omp code.
  """
  def visit_OmpParallel(self, node):
    s = "#pragma omp parallel"
    if node.clauses:
      s += " " + ", ".join(map(str, node.clauses))
    return s

  def visit_OmpParallelFor(self, node):
    s = "#pragma omp parallel for"
    if node.clauses:
      s += " " + ", ".join(map(str, node.clauses))
    return s

  def visit_OmpIfClause(self, node):
    return "if(%s)" % node.exp

  def visit_OmpNumThreadsClause(self, node):
    return "num_threads(%s)" % node.val

  def visit_OmpNoWaitClause(self, node):
    return "nowait"


# ---------------------------------------------------------------------------
# DOT generator

class OmpDotGen(DotGenVisitor):
  """
  Visitor to generator DOT.
  """
  pass
