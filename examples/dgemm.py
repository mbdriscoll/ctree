"""
Computes matrix-matrix products (dgemms) via specialization.
"""

import logging

logging.basicConfig(level=20)

import copy
import numpy as np

from ctree.frontend import get_ast
from ctree.c.nodes import *
from ctree.cpp.nodes import Comment
from ctree.c.types import *
from ctree.simd.macros import *
from ctree.simd.types import *
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

    def _gen_load_c_block(self, rx, ry, lda):
        """
        Return a subtree that loads a block of 'c'.
        """
        stmts = [Comment("Load a block of c")]
        for j in range(0, rx):
            for i in range(0, ry/4):
                stmt = Assign(ArrayRef(ArrayRef(SymbolRef("c"), Constant(i)), Constant(j)),
                              mm256_loadu_pd(Add(SymbolRef("C"), Constant(i*4+j+lda))))
                stmts.append(stmt)
        return Block(stmts)

    def _gen_rank1_update(self, i, rx, ry, cx, cy, lda):
        stmts = []
        for j in range(ry/4):
            stmt = Assign(SymbolRef("a%d"%j),
                          mm256_load_pd( Add(SymbolRef("A"),
                                             Constant(j*4+i*cy)) ))
            stmts.append(stmt)

        for j in range(rx):
            stmt = Assign(SymbolRef("b"),
                          mm256_set1_pd(ArrayRef(SymbolRef("B"),
                                                 Constant(i+j*lda))))
            stmts.append(stmt)

            for k in range(ry/4):
                stmt = Assign(ArrayRef(ArrayRef(SymbolRef("c"), Constant(k)), Constant(j)),
                              mm256_add_pd( ArrayRef(ArrayRef(SymbolRef("c"), Constant(k)), Constant(j)),
                                            mm256_mul_pd(SymbolRef("a%d"%k), SymbolRef("b")) ))
                stmts.append(stmt)

        return Block(stmts)

    def _gen_k_rank1_updates(self, rx, ry, cx, cy, unroll, lda):
        stmts = [Comment("do K rank-1 updates")]
        for i in range(0, ry/4):
            stmts.append(SymbolRef("a%d" % i, m256d()))
        stmts.append(SymbolRef("b", m256d()))

        whyle = While(Lt(SymbolRef("K"), Constant(unroll)), [
            self._gen_rank1_update(i, rx, ry, cx, cy, lda) for i in range(0, ry)
        ])
        stmts.append(whyle)
        return Block(stmts)

    def transform(self, py_ast, program_config):
        """
        Convert the Python AST to a C AST according to the directions
        given in program_config.
        """
        arg_config, tuner_config = program_config
        n, dtype  = arg_config['n'], arg_config['dtype']
        rx, ry = tuner_config['rx'], tuner_config['ry']
        cx, cy = tuner_config['cx'], tuner_config['cy']
        unroll = tuner_config['unroll']

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
        """, copy.deepcopy(template_args))

        reg_template_args = {
            'load_c_block': self._gen_load_c_block(rx, ry, n),
            'k_rank1_updates': self._gen_k_rank1_updates(rx, ry, cx, cy, unroll, n),
        }
        reg_template_args.update(copy.deepcopy(template_args))

        register_dgemm = StringTemplate("""
        void register_dgemm( $A_decl, $B_decl, $C_decl, int K )  {
            __m256d c[$RY/4][$RX];

            $load_c_block

            $k_rank1_updates

            A += $UNROLL*$CY;
            B += $UNROLL;
            K -= $UNROLL;
        }
        """, reg_template_args)

        fast_dgemm = StringTemplate("""
        void fast_dgemm( int M, int N, int K, $A_decl, $B_decl, $C_decl ) {
            static double a[$CX*$CY] __attribute__ ((aligned (16)));

            //  make a local aligned copy of A's block
            for( int j = 0; j < K; j++ )
            for( int i = 0; i < M; i++ )
            a[i+j*$CY] = A[i+j*$lda];

            //  multiply using the copy
            for( int j = 0; j < N; j += $RX )
                for( int i = 0; i < M; i += $RY )
                    register_dgemm( a + i, B + j*$lda, C + i + j*$lda, K );
        }""", template_args)

        fringe_dgemm = StringTemplate("""
        void fringe_dgemm( int M, int N, int K, double *A, double *B, double *C )
        {
            for( int j = 0; j < N; j++ )
               for( int i = 0; i < M; i++ )
                    for( int k = 0; k < K; k++ )
                         C[i+j*$lda] += A[i+k*$lda] * B[k+j*$lda];
        }
        """, copy.deepcopy(template_args))

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
                            fast_dgemm ( I, J, K, $A + i + k*$lda, $B + k + j*$lda, $C + i + j*$lda );
                        else
                            fringe_dgemm( I, J, K, $A + i + k*$lda, $B + k + j*$lda, $C + i + j*$lda );
                        k += K;
                    }
                    j += J;
                }
                i += I;
            }
        }
        """, copy.deepcopy(template_args))

        tree = CFile("generated", [
            preamble,
            register_dgemm,
            fast_dgemm,
            fringe_dgemm,
            dgemm,
        ])

        with open("graph.dot", 'w') as f:
            f.write( to_dot(tree) )

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
