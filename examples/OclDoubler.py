"""
Parses the python AST below, transforms it to C, JITs it, and runs it.
"""

import logging

logging.basicConfig(level=20)

import numpy as np

from pycl import (
    clCreateProgramWithSource,
    clCreateContextFromType,
    clCreateCommandQueue,
    buffer_from_ndarray,
    buffer_to_ndarray,
    cl_mem,
)

from ctree.c.nodes import *
from ctree.c.types import *
from ctree.cpp.nodes import *
from ctree.ocl.nodes import *
from ctree.ocl.types import *
from ctree.ocl.macros import *
from ctree.templates.nodes import FileTemplate
from ctree.transformations import *
from ctree.frontend import get_ast
from ctree.jit import LazySpecializedFunction
from ctree.jit import ConcreteSpecializedFunction
from ctree.types import get_ctree_type

# ---------------------------------------------------------------------------
# Specializer code

class OpFunction(ConcreteSpecializedFunction):
    def __init__(self):
        self.cl_context = clCreateContextFromType()
        self.cl_queue = clCreateCommandQueue(self.cl_context)

    def finalize(self, cl_kernel):
        self.kernel = cl_kernel
        return self

    def __call__(self, A):
        queue = self.cl_queue
        buf, in_evt = buffer_from_ndarray(queue, A, blocking=False)
        run_evt = self.kernel(buf).on(queue, len(A), wait_for=in_evt)
        B, out_evt = buffer_to_ndarray(queue, buf, like=A, wait_for=run_evt)
        return B


class OpTranslator(LazySpecializedFunction):
    def args_to_subconfig(self, args):
        """
        Analyze arguments and return a 'subconfig', a hashable object
        that classifies them. Arguments with identical subconfigs
        might be processed by the same generated code.
        """
        A = args[0]
        return len(A), A.dtype, A.ndim, A.shape

    def transform(self, py_ast, program_config):
        """
        Convert the Python AST to a C AST according to the directions
        given in program_config.
        """
        fn = OpFunction()

        len_A, A_dtype, A_ndim, A_shape = program_config[0]
        A_type = NdPointer(A_dtype, A_ndim, A_shape)

        apply_one = PyBasicConversions().visit(py_ast.body[0])
        apply_one.return_type = A_type.get_base_type()
        apply_one.params[0].type = A_type.get_base_type()

        apply_kernel = FunctionDecl(Void(), "apply_kernel",
            params=[SymbolRef("A", A_type).set_global()],
            defn=[
                Assign(SymbolRef("i", Int()),
                       FunctionCall(SymbolRef("get_global_id"), [Constant(0)])),
                Assign(ArrayRef(SymbolRef("A"), SymbolRef("i")),
                       FunctionCall(SymbolRef("apply"),
                                    [ArrayRef(SymbolRef("A"), SymbolRef("i"))])),
            ]
        ).set_kernel()

        kernel = OclFile("kernel", [apply_one, apply_kernel])

        program = clCreateProgramWithSource(fn.cl_context, kernel.codegen()).build()
        cl_kernel = program['apply_kernel']
        cl_kernel.argtypes = cl_mem,

        with open("graph.dot", 'w') as f:
          f.write( kernel.to_dot() )

        return fn.finalize(cl_kernel)


class ArrayOp(object):
    """
    A class for managing independent operation on elements
    in numpy arrays.
    """

    def __init__(self):
        """Instantiate translator."""
        self.translator = OpTranslator(get_ast(self.apply))

    def __call__(self, A):
        """Apply the operator to the arguments via a generated function."""
        return self.translator(A)

    def interpret(self, A):
        return np.vectorize(self.apply)(A)


# ---------------------------------------------------------------------------
# User code

class Doubler(ArrayOp):
    """Double elements of the array."""

    @staticmethod
    def apply(x):
        return x * 2


class Squarer(ArrayOp):
    """Double elements of the array."""

    @staticmethod
    def apply(x):
        return x * x


def main():
    data = np.arange(1024, dtype=np.float32)

    # squaring floats
    squarer = Squarer()
    actual   = squarer(data)
    expected = squarer.interpret(data)
    np.testing.assert_array_equal(actual, expected)
    print("Squarer works.")

    # doubling floats
    doubler = Doubler()
    actual = doubler(data)
    expected = doubler.interpret(data)
    np.testing.assert_array_equal(actual, expected)
    print("Doubler works.")

if __name__ == '__main__':
    main()
