"""
Demonstrates use of OpenMP.
"""

import logging

logging.basicConfig(level=20)

import numpy as np

from ctree.nodes import Project
from ctree.c.nodes import *
from ctree.c.macros import *
from ctree.cpp.nodes import *
from ctree.omp.nodes import *
from ctree.omp.macros import *
from ctree.jit import LazySpecializedFunction, ConcreteSpecializedFunction
from ctypes import CFUNCTYPE

# ---------------------------------------------------------------------------
# Specializer code


class GreeterFunction(ConcreteSpecializedFunction):

    def finalize(self, tree, entry_name, entry_type):
        self._c_function = self._compile(entry_name, tree, entry_type)
        return self

    def __call__(self):
        self._c_function()

class GreeterTranslator(LazySpecializedFunction):
    def transform(self, py_ast, program_config):
        tree = CFile("generated", [
            CppInclude("omp.h"),
            CppInclude("stdio.h"),
            FunctionDecl(None, "hello",
                         params=[],
                         defn=[
                             OmpParallel( [OmpNumThreadsClause(Constant(4))] ),
                             printf(r"Hello from thread %d of %d.\n", \
                                    omp_get_thread_num(), omp_get_num_threads()),
                         ]
            ),
        ])
        # entry_point_typesig = tree.find(FunctionDecl, name="hello").get_type().as_ctype()
        entry_type = CFUNCTYPE(None)

        fn = GreeterFunction()

        return fn.finalize(Project([tree]), "hello", entry_type)


class ParallelGreeter(object):
    def __init__(self):
        """Instantiate translator."""
        self.c_hello = GreeterTranslator(None)

    def __call__(self):
        """Apply the operator to the arguments via a generated function."""
        return self.c_hello()


# ---------------------------------------------------------------------------
# User code

def main():
    c_hello = ParallelGreeter()
    c_hello()
    print("Done.")

if __name__ == '__main__':
    main()
