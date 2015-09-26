"""
Computes matrix-matrix products via specialization.
"""

import logging
from ctree.nodes import Project

logging.basicConfig(level=60)

import copy
import numpy as np
import ctypes as ct
import inspect

from ctree.c.nodes import *
from ctree.cpp.nodes import CppComment
from ctree.types import *
from ctree.simd.macros import *
from ctree.simd.types import *
from ctree.templates.nodes import StringTemplate
from ctree.transformations import *
from ctree.jit import LazySpecializedFunction, ConcreteSpecializedFunction
from ctree.metrics.watts_up_reader import WattsUpReader

def MultiArrayRef(name, *idxs):
    """
    Given a string and a list of ints, produce the chain of
    array-ref expressions:

    >>> MultiArrayRef('foo', Constant(1), Constant(2), Constant(3)).codegen()
    'foo[1][2][3]'
    """
    tree = ArrayRef(SymbolRef(name), idxs[0])
    for idx in idxs[1:]:
        tree = ArrayRef(tree, Constant(idx))
    return tree


def hello():
    return "hello"


class DgemmTranslator(LazySpecializedFunction):
    def __init__(self):
        self._current_config = None
        super(DgemmTranslator, self).__init__(ast.parse(inspect.getsource(hello)), "dgemm")

    def get_tuning_driver(self):
        from ctree.opentuner.driver import OpenTunerDriver
        from opentuner.search.manipulator import ConfigurationManipulator
        from opentuner.search.manipulator import IntegerParameter
        from opentuner.search.manipulator import PowerOfTwoParameter
        from opentuner.search.objective import MinimizeTime, MinimizeEnergy

        manip = ConfigurationManipulator()
        manip.add_parameter(PowerOfTwoParameter("rx", 1, 8))
        manip.add_parameter(PowerOfTwoParameter("ry", 1, 8))
        manip.add_parameter(IntegerParameter("cx", 8, 32))
        manip.add_parameter(IntegerParameter("cy", 8, 32))

        return OpenTunerDriver(manipulator=manip, objective=MinimizeTime())

    def args_to_subconfig(self, args):
        """
        Analyze arguments and return a 'subconfig', a hashable object
        that classifies them. Arguments with identical subconfigs
        might be processed by the same generated code.
        """
        C, A, B, duration = args
        n = len(A)
        assert C.shape == A.shape == B.shape == (n, n)
        assert A.dtype == B.dtype == C.dtype
        return {
            'n': n,
            'dtype': A.dtype,
        }

    def _gen_load_c_block(self, rx, ry, lda):
        """
        Return a subtree that loads a block of 'c'.
        """
        stmts = [CppComment("Load a block of c")]
        for j in range(rx):
            for i in range(ry/4):
                stmt = Assign(MultiArrayRef("c", Constant(i), Constant(j)),
                              mm256_loadu_pd(Add(SymbolRef("C"), Constant(i*4+j*lda))))
                stmts.append(stmt)
        return Block(stmts)

    def _gen_store_c_block(self, rx, ry, lda):
        """
        Return a subtree that loads a block of 'c'.
        """
        stmts = [CppComment("Store the c block")]
        for j in range(rx):
            for i in range(ry/4):
                stmt = mm256_storeu_pd(Add(SymbolRef("C"), Constant(i*4+j*lda)),
                                      MultiArrayRef("c", Constant(i), Constant(j)))
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
                stmt = Assign(MultiArrayRef("c", Constant(k), Constant(j)),
                              mm256_add_pd( MultiArrayRef("c", Constant(k), Constant(j)),
                                            mm256_mul_pd(SymbolRef("a%d"%k), SymbolRef("b")) ))
                stmts.append(stmt)
        return Block(stmts)

    def _gen_k_rank1_updates(self, rx, ry, cx, cy, unroll, lda):
        stmts = [CppComment("do K rank-1 updates")]
        for i in range(ry/4):
            stmts.append(SymbolRef("a%d" % i, m256d()))
        stmts.append(SymbolRef("b", m256d()))
        stmts.extend(self._gen_rank1_update(i, rx, ry, cx, cy, lda) for i in range(unroll))
        return Block(stmts)

    def transform(self, py_ast, program_config):
        """
        Convert the Python AST to a C AST according to the directions
        given in program_config.
        """
        self._current_config = program_config

        arg_config, tuner_config = program_config
        n, dtype = arg_config['n'], arg_config['dtype']
        rx, ry = tuner_config['rx']*4, tuner_config['ry']*4
        cx, cy = tuner_config['cx']*4, tuner_config['cy']*4
        unroll = tuner_config['ry']*4

        array_type = np.ctypeslib.ndpointer(dtype, 2, (n, n))

        A = SymbolRef("A", array_type())
        B = SymbolRef("B", array_type())
        C = SymbolRef("C", array_type())

        N = Constant(n)
        RX, RY = Constant(rx), Constant(ry)
        CX, CY = Constant(cx), Constant(cy)
        UNROLL = Constant(unroll)

        template_args = {
            "A_decl": A.copy(declare=True),
            "B_decl": B.copy(declare=True),
            "C_decl": C.copy(declare=True),
            "RX": RX,
            "RY": RY,
            "CX": CX,
            "CY": CY,
            "UNROLL": UNROLL,
            "lda": N,
        }

        preamble = StringTemplate("""
        #include <immintrin.h>
        #include <stdio.h>
        #define min(x,y) (((x)<(y))?(x):(y))
        """, copy.deepcopy(template_args))

        reg_template_args = {
            'load_c_block': self._gen_load_c_block(rx, ry, n),
            'store_c_block': self._gen_store_c_block(rx, ry, n),
            'k_rank1_updates': self._gen_k_rank1_updates(rx, ry, cx, cy, unroll, n),
        }
        reg_template_args.update(copy.deepcopy(template_args))

        register_dgemm = StringTemplate("""
        void register_dgemm( $A_decl, $B_decl, $C_decl, int K )  {
            __m256d c[$RY/4][$RX];

            $load_c_block

            while ( K >= $UNROLL ) {
              $k_rank1_updates

              A += $UNROLL*$CY;
              B += $UNROLL;
              K -= $UNROLL;
            }

            $store_c_block
        }
        """, reg_template_args)

        fast_dgemm = StringTemplate("""
        void fast_dgemm( int M, int N, int K, $A_decl, $B_decl, $C_decl ) {
            static double a[$CX*$CY] __attribute__ ((aligned (32)));

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
        void fringe_dgemm( int M, int N, int K, $A_decl, $B_decl, $C_decl )
        {
            for( int j = 0; j < N; j++ )
               for( int i = 0; i < M; i++ )
                    for( int k = 0; k < K; k++ )
                         C[i+j*$lda] += A[i+k*$lda] * B[k+j*$lda];
        }
        """, copy.deepcopy(template_args))

        wall_time = StringTemplate("""
        #include <sys/time.h>

        double wall_time () {
          struct timeval t;
          gettimeofday (&t, NULL);
          return 1.*t.tv_sec + 1.e-6*t.tv_usec;
        }

        """, {})

        dgemm = StringTemplate("""
        int align( int x, int y ) { return x <= y ? x : (x/y)*y; }

        void dgemm($C_decl, $A_decl, $B_decl, double *duration) {
            double start_time = wall_time();

            for( int i = 0; i < $lda; ) {
                int I = align( min( $lda-i, $CY ), $RY );
                for( int j = 0; j < $lda; ) {
                    int J = align( $lda-j, $RX );
                    for( int k = 0; k < $lda; ) {
                        int K = align( min( $lda-k, $CX ), $UNROLL );
                        if( (I%$RY) == 0 && (J%$RX) == 0 && (K%$UNROLL) == 0 )
                            fast_dgemm ( I, J, K, A + i + k*$lda, B + k + j*$lda, C + i + j*$lda );
                        else
                            fringe_dgemm( I, J, K, A + i + k*$lda, B + k + j*$lda, C + i + j*$lda );
                        k += K;
                    }
                    j += J;
                }
                i += I;
            }

            // report time back for tuner
            *duration = wall_time() - start_time;
        }
        """, copy.deepcopy(template_args))

        tree = CFile("generated", [
            preamble,
            wall_time,
            register_dgemm,
            fast_dgemm,
            fringe_dgemm,
            dgemm,
        ])

        c_dgemm = CFile("generated", [tree])
        return [c_dgemm]

    def finalize(self, transform_result, program_config):
        c_dgemm = transform_result[0]
        proj = Project([c_dgemm])

        arg_config, tuner_config = program_config
        n, dtype = arg_config['n'], arg_config['dtype']
        array_type = np.ctypeslib.ndpointer(dtype, 2, (n, n))
        entry_type = ct.CFUNCTYPE(None, array_type, array_type, array_type, POINTER(c_double))


        concrete_Fn = ConcreteDgemm()
        return concrete_Fn.finalize("dgemm", proj, entry_type)


class ConcreteDgemm(ConcreteSpecializedFunction):
    def finalize(self, entry_point_name, project_node, entry_typesig):
        self._c_function = self._compile(entry_point_name, project_node, entry_typesig)
        return self

    def __call__(self, C, A, B, duration):
        return self._c_function(C, A, B, duration)


class SquareDgemm(object):
    def __init__(self):
        """Instantiate translator."""
        self.c_dgemm = DgemmTranslator()

    def __call__(self, A, B):
        """C = A * B"""

        C = np.zeros(shape=A.shape, dtype=A.dtype)
        meter = Meter()
        meter.start_recording()
        self.c_dgemm(C, A, B, ct.byref(meter.time_meter))

        joules = meter.energy_value()
        seconds = meter.time_value()
        self.c_dgemm.report(time=seconds, energy=joules)
        return C, seconds, joules, self.c_dgemm._current_config


class Meter(object):
    def __init__(self, use_energy=False):
        self.time_meter = c_double()
        self.use_energy = use_energy
        self.energy_meter = WattsUpReader() if self.use_energy else None

    def start_recording(self):
        if self.use_energy:
            self.energy_meter.start_recording()

    def time_value(self):
        return self.time_meter.value

    def energy_value(self):
        if self.use_energy:
            return self.energy_meter.get_recording()[0].joules
        else:
            return 0.0


def main():
    n = 2048
    c_dot = SquareDgemm()

    A = np.random.rand(n, n)
    B = np.random.rand(n, n)
    C_expected = np.dot(A.T, B.T)

    best_joules = float('inf')
    for i in range(1000):
        C_actual, seconds, joules, config = c_dot(A, B)
        np.testing.assert_almost_equal(C_actual.T, C_expected)

        best_indicator = "*** new best ***" if joules < best_joules else ""
        best_joules = min(best_joules, joules)

        ticks = min(40, int(joules / 10.0))
        print("trial %s %s took %f sec, used %s joules: %s %s" %
              (str(i).rjust(3), str(config[1]).ljust(38), seconds, str(joules).rjust(5),
               ('#' * ticks).ljust(40), best_indicator))

        del C_actual

    print("Done.")


if __name__ == '__main__':
    main()
