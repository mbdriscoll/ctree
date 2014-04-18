import unittest

from ctree.omp.nodes import *
from ctree.omp.macros import *
from ctree.c.nodes import *


class TestOmpCodegen(unittest.TestCase):
    def test_parallel(self):
        node = OmpParallel()
        self.assertEqual(str(node), "#pragma omp parallel")

    def test_parallel_for(self):
        node = OmpParallelFor()
        self.assertEqual(str(node), "#pragma omp parallel for")

    def test_nowait(self):
        node = OmpParallelFor(clauses=[OmpNoWaitClause()])
        self.assertEqual(str(node), "#pragma omp parallel for nowait")

    def test_if_exp(self):
        node = OmpParallel(clauses=[OmpIfClause(SymbolRef("i"))])
        self.assertEqual(str(node), "#pragma omp parallel if(i)")

    def test_num_threads(self):
        node = OmpParallel([OmpNumThreadsClause(Constant(3))])
        self.assertEqual(str(node), "#pragma omp parallel num_threads(3)")

    def test_ivdep(self):
        node = OmpIvDep()
        self.assertEqual(str(node), "#pragma IVDEP")

    def test_no_semicolons(self):
        """There shouldn't be semicolons after Omp statementss."""
        node = Block([OmpParallel(), Assign(SymbolRef("x"), Constant(3))])
        self.assertEqual(str(node), """{
    #pragma omp parallel
    x = 3;
}""")

    def test_get_wtime(self):
        node = omp_get_wtime()
        self.assertEqual(str(node), "omp_get_wtime()")
