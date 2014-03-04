"""
Code generation for OpenMP.
"""

from ctree.codegen import CodeGenVisitor


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

  def visit_OmpIvDep(self, node):
    s = "#pragma IVDEP"
    if node.clauses:
      s += " " + ", ".join(map(str, node.clauses))
    return s

  def visit_OmpIfClause(self, node):
    return "if(%s)" % node.exp

  def visit_OmpNumThreadsClause(self, node):
    return "num_threads(%s)" % node.val

  def visit_OmpNoWaitClause(self, node):
    return "nowait"
