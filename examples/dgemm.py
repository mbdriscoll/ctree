"""
Computes matrix-matrix products (dgemms) via specialization.
"""

import logging

logging.basicConfig(level=20)

import numpy as np

from ctree.frontend import get_ast
from ctree.c.nodes import *
from ctree.c.types import *
from ctree.templates.nodes import StringTemplate
from ctree.dotgen import to_dot
from ctree.transformations import *
from ctree.jit import LazySpecializedFunction
from ctree.types import get_ctree_type

class DgemmTranslator(LazySpecializedFunction):
    def __init__(self):
        super(DgemmTranslator, self).__init__(None, "dgemm")

    def args_to_subconfig(self, args):
        """
        Analyze arguments and return a 'subconfig', a hashable object
        that classifies them. Arguments with identical subconfigs
        might be processed by the same generated code.
        """
        C, A, B = args
        n = len(A)
        assert C.shape == A.shape == B.shape == (n,n)
        assert A.dtype == B.dtype == C.dtype
        return {
            'n': n,
            'dtype': A.dtype,
        }

    def transform(self, py_ast, program_config):
        """
        Convert the Python AST to a C AST according to the directions
        given in program_config.
        """
        arg_config, tuner_config = program_config
        n, dtype  = arg_config['n'], arg_config['dtype']

        elem_type = get_ctree_type(dtype)
        array_type = NdPointer(dtype, 2, (n,n))

        dgemm_typesig = FuncType(Void(), [array_type, array_type, array_type])

        A = SymbolRef("A", array_type)
        B = SymbolRef("B", array_type)
        C = SymbolRef("C", array_type)

        template_args = {
            "A_decl": A.copy(declare=True),
            "B_decl": B.copy(declare=True),
            "C_decl": C.copy(declare=True),
        }

        tree = CFile("generated", [
            StringTemplate("""\
            void dgemm($C_decl, $A_decl, $B_decl) {
            }
            """, template_args),
        ])

        return Project([tree]), dgemm_typesig.as_ctype()


class SquareDgemm(object):
    def __init__(self):
        """Instantiate translator."""
        self.c_dgemm = DgemmTranslator()

    def __call__(self, C, A, B):
        """C = A * B"""
        return self.c_dgemm(C, A, B)


def main():
    n = 16
    c_dgemm = SquareDgemm()

    A = np.random.rand(n, n)
    B = np.random.rand(n, n)
    C_actual = np.random.rand(n, n)
    C_expected = A * B

    c_dgemm(C_actual, A, B)

    np.testing.assert_array_equal(C_actual, C_expected)
    print("Success.")


if __name__ == '__main__':
    main()
