import unittest
from textwrap import dedent

from ctypes import c_int

from ctree.omp.nodes import *
from ctree.omp.macros import *
from ctree.c.nodes import *

from util import CtreeTest

class TestOmpCodegen(CtreeTest):
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
        self.assertEqual(str(node), dedent("""\
        {
            #pragma omp parallel
            x = 3;
        }"""))

    def test_get_wtime(self):
        node = omp_get_wtime()
        self.assertEqual(str(node), "omp_get_wtime()")

    def test_sections_1(self):
        node = OmpParallelSections(sections=[
                OmpSection(body=[
                    Assign(SymbolRef("i", c_int()), Constant(2)),
                ]),
        ])
        self._check_code(node, """\
        #pragma omp parallel sections
        {
            #pragma omp section
            {
                int i = 2;
            }
        }""")


class TestOmpMacros(CtreeTest):
    def test_num_threads(self):
        tree = omp_get_num_threads()
        self._check_code(tree, "omp_get_num_threads()")

    def test_thread_num(self):
        tree = omp_get_thread_num()
        self._check_code(tree, "omp_get_thread_num()")

    def test_get_wtime(self):
        tree = omp_get_wtime()
        self._check_code(tree, "omp_get_wtime()")

    def test_include(self):
        tree = IncludeOmpHeader()
        self._check_code(tree, "#include <omp.h>")
