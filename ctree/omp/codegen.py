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

    def visit_OmpParallelSections(self, node):
        s = "#pragma omp parallel sections"
        if node.clauses:
            s += " " + ", ".join(map(str, node.clauses))
        s += "\n%s%s" % (self._tab(), self._genblock(node.sections))
        return s

    def visit_OmpSection(self, node):
        s = "#pragma omp section"
        if node.clauses:
            s += " " + ", ".join(map(str, node.clauses))
        s += "\n%s%s" % (self._tab(), self._genblock(node.body))
        return s

    def visit_OmpIfClause(self, node):
        return "if(%s)" % node.exp

    def visit_OmpNumThreadsClause(self, node):
        return "num_threads(%s)" % node.val

    def visit_OmpNoWaitClause(self, node):
        return "nowait"

    def visit_OmpIvDep(self, node):
        s = "#pragma IVDEP"
        if node.clauses:
          s += " " + ", ".join(map(str, node.clauses))
        return s     
