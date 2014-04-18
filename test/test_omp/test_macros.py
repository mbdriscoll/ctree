import unittest

from ctree.omp.macros import *


class TestOmpMacros(unittest.TestCase):
    def _check(self, actual, expected):
        self.assertEqual(actual.codegen(), expected)

    def test_get_num_threads(self):
        self._check(omp_get_num_threads(), "omp_get_num_threads()")

    def test_get_thread_num(self):
        self._check(omp_get_thread_num(), "omp_get_thread_num()")

    def test_get_wtime(self):
        self._check(omp_get_wtime(), "omp_get_wtime()")

    def test_include_omp_header(self):
        self._check(IncludeOmpHeader(), "#include <omp.h>")
