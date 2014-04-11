"""
Code generator for the expression A*(B+C), where A, B, and C are vectors
and all operations are element-wise.
"""

import logging

logging.basicConfig(level=20)

import numpy as np

from ctree.frontend import get_ast
from ctree.c.nodes import *
from ctree.c.types import *
from ctree.templates.nodes import *
from ctree.dotgen import to_dot
from ctree.transformations import *
from ctree.jit import LazySpecializedFunction

# ---------------------------------------------------------------------------
# Specializer code

class OpTranslator(LazySpecializedFunction):
    def get_tuning_driver(self):
        from ctree.tune import BruteForceTuningDriver
        from ctree.tune import MinimizeTime
        from ctree.tune import IntegerParameter
        from ctree.tune import BooleanParameter

        params = [
            IntegerParameter("mode", 1, 3),
            BooleanParameter("apply_distributive_law"),
        ]

        objective = MinimizeTime()
        return BruteForceTuningDriver(params, objective)

    def args_to_subconfig(self, args):
        """
        Analyze arguments and return a 'subconfig', a hashable object
        that classifies them. Arguments with identical subconfigs
        might be processed by the same generated code.
        """
        A = args[0]
        return {
            'A_ptr': NdPointer.to(A),
            'A_len': len(A),
            'A_dtype': A.dtype,
        }

    def transform(self, py_ast, program_config):
        """
        Convert the Python AST to a C AST according to the directions
        given in program_config.
        """
        arg_config, tuner_config = program_config

        tree = VVMul(Vec("A"), VVAdd(Vec("B"), Vec("C")))
        if tuner_config['apply_distributive_law']:
            ...

        A_ptr = arg_config['A_ptr']
        A_len = arg_config['A_len']
        A_dtype = arg_config['A_dtype']
        mode = tuner_config['mode']

        if   mode == 1: return self._transform_cpu_cpu_serial(A_ptr, A_len, A_dtype)
        if   mode == 2: return self._transform_cpu_cpu_parallel(A_ptr, A_len, A_dtype)
        else:
            raise ValueError("Unrecognized implementation mode: %d" % mode)

    def _transform_cpu_cpu_serial(self, A_ptr, A_len, A_dtype):
        tmpB = np.zeros(A_len, dtype=A_dtype)
        tmpC = np.zeros(A_len, dtype=A_dtype)

        tree = CFile("generated", [
            StringTemplate("""\
            void op(float *A, float *B, float *C, float *ans, float *tmpB, float *tmpC) {
                // D = A*B+A*C elementwise
                for (int i = 0; i < $n; i++) {
                    tmpB[i] = A[i] * B[i];
                }

                for (int i = 0; i < $n; i++) {
                    tmpC[i] = A[i] * C[i];
                }

                for (int i = 0; i < $n; i++) {
                    ans[i] = tmpB[i] + tmpC[i];
                }
            }
            """, {'n' : Constant(A_len)}),
        ])

        extra_args = (tmpB, tmpC)
        entry_point_typesig = FuncType(Void(), [A_ptr] * 6).as_ctype()
        return Project([tree]), entry_point_typesig, extra_args

    def _transform_cpu_cpu_parallel(self, A_ptr, A_len, A_dtype):
        import ctree.omp

        tmpB = np.empty(A_len, dtype=A_dtype)
        tmpC = np.empty(A_len, dtype=A_dtype)

        tree = CFile("generated", [
            StringTemplate("""\
            #include <omp.h>
            void op(float *A, float *B, float *C, float *ans, float *tmpB, float *tmpC) {
                // D = A*B+A*C elementwise
                omp_set_num_threads(2);

                #pragma omp parallel sections
                {
                    #pragma omp section
                    {
                        for (int i = 0; i < $n; i++)
                            tmpB[i] = A[i] * B[i];
                    }

                    #pragma omp section
                    {
                        for (int i = 0; i < $n; i++)
                            tmpC[i] = A[i] * C[i];
                    }
                }

                for (int i = 0; i < $n; i++)
                    ans[i] = tmpB[i] + tmpC[i];
            }
            """, {'n' : Constant(A_len)}),
        ])

        extra_args = (tmpB, tmpC)
        entry_point_typesig = FuncType(Void(), [A_ptr] * 6).as_ctype()
        return Project([tree]), entry_point_typesig, extra_args


    def _transform_gpu_gpu_serial(self, A_ptr, A_len, A_dtype):
        tmpB = np.zeros(A_len, dtype=A_dtype)
        tmpC = np.zeros(A_len, dtype=A_dtype)

        tree = CFile("generated", [
            StringTemplate("""\
            void op(float *A, float *B, float *C, float *ans, float *tmpB, float *tmpC) {
                // D = A*B+A*C elementwise
                for (int i = 0; i < $n; i++) {
                    tmpB[i] = A[i] * B[i];
                }

                for (int i = 0; i < $n; i++) {
                    tmpC[i] = A[i] * C[i];
                }

                for (int i = 0; i < $n; i++) {
                    ans[i] = tmpB[i] + tmpC[i];
                }
            }
            """, {'n' : Constant(A_len)}),
        ])

        extra_args = (tmpB, tmpC)
        entry_point_typesig = FuncType(Void(), [A_ptr] * 6).as_ctype()
        return Project([tree]), entry_point_typesig, extra_args


class Op(object):
    """
    A class for managing independent operation on elements
    in numpy arrays.
    """

    def __init__(self):
        """Instantiate translator."""
        self.c_op = OpTranslator(None, "op")

    def __call__(self, a, b, c):
        """Apply the operator to the arguments via a generated function."""
        answer = np.zeros_like(a)
        self.c_op(a, b, c, answer)
        return answer


# ---------------------------------------------------------------------------
# User code

def py_op(a, b, c):
    return a * (b + c)

def main():
    n = 12
    c_op = Op()

    # doubling doubles
    for i in range(2):
      a = np.arange(n, dtype=np.float32)
      b = np.ones(n, dtype=np.float32)
      c = np.ones(n, dtype=np.float32)

      actual = c_op(a, b, c)
      expected = py_op(a, b, c)

      np.testing.assert_array_equal(actual, expected)

    print("Success.")


if __name__ == '__main__':
    main()
