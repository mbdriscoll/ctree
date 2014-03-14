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

    def get_tuning_driver(self):
        from ctree.opentuner.driver import OpenTunerDriver
        from opentuner.search.manipulator import ConfigurationManipulator
        from opentuner.search.manipulator import IntegerParameter
        from opentuner.search.objective import MinimizeTime

        manip = ConfigurationManipulator()
        manip.add_parameter(IntegerParameter("rx", 1, 16))
        manip.add_parameter(IntegerParameter("ry", 1, 16))
        manip.add_parameter(IntegerParameter("cx", 16, 2048))
        manip.add_parameter(IntegerParameter("cy", 16, 2048))
        manip.add_parameter(IntegerParameter("unroll", 1, 16))

        return OpenTunerDriver(manipulator=manip, objective=MinimizeTime())

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
        rx, ry = tuner_config.data['rx'], tuner_config.data['ry']
        cx, cy = tuner_config.data['cx'], tuner_config.data['cy']
        unroll = tuner_config.data['unroll']
        # TODO: tuner_config should just be a dictionary, not needing .data

        elem_type = get_ctree_type(dtype)
        array_type = NdPointer(dtype, 2, (n,n))

        dgemm_typesig = FuncType(Void(), [array_type, array_type, array_type])

        A = SymbolRef("A", array_type)
        B = SymbolRef("B", array_type)
        C = SymbolRef("C", array_type)

        N = Constant(n)
        RX, RY = Constant(rx), Constant(ry)
        CX, CY = Constant(cx), Constant(cy)
        UNROLL = Constant(unroll)

        template_args = {
            "A_decl": A.copy(declare=True),
            "B_decl": B.copy(declare=True),
            "C_decl": C.copy(declare=True),
            "A": A.copy(),
            "B": B.copy(),
            "C": C.copy(),
            "RX": RX,
            "RY": RY,
            "CX": CX,
            "CY": CY,
            "UNROLL": UNROLL,
            "lda": N,
        }

        preamble =  StringTemplate("""
        #include <immintrin.h>
        #define min(x,y) (((x)<(y))?(x):(y))
        """, {})

        fringe_dgemm = StringTemplate("""
        void fringe_dgemm( int lda, int M, int N, int K, double *A, double *B, double *C )
        {
            for( int j = 0; j < N; j++ )
               for( int i = 0; i < M; i++ )
                    for( int k = 0; k < K; k++ )
                         C[i+j*lda] += A[i+k*lda] * B[k+j*lda];
        }
        """, {})

        dgemm =  StringTemplate("""
        int align( int x, int y ) { return x <= y ? x : (x/y)*y; }

        void dgemm($C_decl, $A_decl, $B_decl) {
            for( int i = 0; i < $lda; ) {
                int I = align( min( $lda-i, $CY ), $RY );
                for( int j = 0; j < $lda; ) {
                    int J = align( $lda-j, $RX );
                    for( int k = 0; k < $lda; ) {
                        int K = align( min( $lda-k, $CX ), $UNROLL );
                        if( (I%$RY) == 0 && (J%$RX) == 0 && (K%$UNROLL) == 0 )
                            fast_dgemm ( $lda, I, J, K, $A + i + k*$lda, $B + k + j*$lda, $C + i + j*$lda );
                        else
                            fringe_dgemm( $lda, I, J, K, $A + i + k*$lda, $B + k + j*$lda, $C + i + j*$lda );
                        k += K;
                    }
                    j += J;
                }
                i += I;
            }
        }
        """, template_args)

        tree = CFile("generated", [
            preamble,
            fringe_dgemm,
            dgemm,
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
