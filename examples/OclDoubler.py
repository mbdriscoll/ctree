"""
Parses the python AST below, transforms it to C, JITs it, and runs it.
"""

import logging

logging.basicConfig(level=20)

import numpy as np
import ctypes as ct
import pycl as cl

from ctree.c.nodes import *
from ctree.c.types import *
from ctree.cpp.nodes import *
from ctree.ocl.nodes import *
from ctree.ocl.types import *
from ctree.ocl.macros import *
from ctree.templates.nodes import StringTemplate
from ctree.transformations import *
from ctree.frontend import get_ast
from ctree.jit import LazySpecializedFunction
from ctree.jit import ConcreteSpecializedFunction
from ctree.types import get_ctree_type

# ---------------------------------------------------------------------------
# Specializer code

class OpFunction(ConcreteSpecializedFunction):
    def __init__(self):
        self.context = cl.clCreateContextFromType()
        self.queue = cl.clCreateCommandQueue(self.context)

    def finalize(self, kernel, tree, entry_name, entry_type):
        self.kernel = kernel
        self._c_function = self._compile(entry_name, tree, entry_type)
        return self

    def __call__(self, A):
        buf, evt = cl.buffer_from_ndarray(self.queue, A, blocking=False)
        self._c_function(self.context, self.queue, self.kernel, buf)
        B, evt = cl.buffer_to_ndarray(self.queue, buf, like=A)
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
                If(Lt(SymbolRef("i"), Constant(len_A)), [
                    Assign(ArrayRef(SymbolRef("A"), SymbolRef("i")),
                           FunctionCall(SymbolRef("apply"),
                                        [ArrayRef(SymbolRef("A"), SymbolRef("i"))])),
                ], []),
            ]
        ).set_kernel()

        kernel = OclFile("kernel", [apply_one, apply_kernel])

        control = StringTemplate(r"""
        #include <OpenCL/opencl.h>
        void apply_all(cl_context ctx, cl_command_queue queue, cl_kernel kernel, cl_mem buf) {
            size_t global = $n;
            size_t local = 32;
            clSetKernelArg(kernel, 0, sizeof(cl_mem), &buf);
            clEnqueueNDRangeKernel(queue, kernel, 1, NULL, &global, &local, 0, NULL, NULL);

        }
        """, {'n': Constant(len_A + 32 - (len_A % 32))})

        proj = Project([kernel, CFile("generated", [control])])
        fn = OpFunction()

        program = cl.clCreateProgramWithSource(fn.context, kernel.codegen()).build()
        apply_kernel_ptr = program['apply_kernel']

        entry_type = ct.CFUNCTYPE(ct.c_void_p, cl.cl_context, cl.cl_command_queue, cl.cl_kernel, cl.cl_mem)
        return fn.finalize(apply_kernel_ptr, proj, "apply_all", entry_type)


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
# user code

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
    data = np.arange(123, dtype=np.float32)

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
