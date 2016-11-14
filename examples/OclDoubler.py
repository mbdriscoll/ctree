"""
Parses the python AST below, transforms it to C, JITs it, and runs it.
"""

import logging

logging.basicConfig(level=20)

import numpy as np
import ctypes as ct
import pycl as cl

import ctree.np
from ctree.c.nodes import *
from ctree.cpp.nodes import *
from ctree.ocl.nodes import *
from ctree.ocl.types import *
from ctree.ocl.macros import *
from ctree.templates.nodes import StringTemplate
from ctree.transformations import *
from ctree.frontend import get_ast
from ctree.jit import LazySpecializedFunction
from ctree.jit import ConcreteSpecializedFunction

from ctree import browser_show_ast

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
        self._c_function(self.queue, self.kernel, buf)
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
        return np.ctypeslib.ndpointer(A.dtype, A.ndim, A.shape)

    def transform(self, py_ast, program_config):
        """
        Convert the Python AST to a C AST according to the directions
        given in program_config.
        """
        A = program_config[0]
        len_A = np.prod(A._shape_)
        inner_type = A._dtype_.type()
        # browser_show_ast(py_ast,'tmp.png')
        apply_one = PyBasicConversions().visit(py_ast.body[0])
        apply_one.name = 'apply'
        apply_one.return_type = inner_type
        apply_one.params[0].type = inner_type

        apply_kernel = FunctionDecl(None, "apply_kernel",
            params=[SymbolRef("A", A()).set_global()],
            defn=[
                Assign(SymbolRef("i", ct.c_int()), get_global_id(0)),
                If(Lt(SymbolRef("i"), Constant(len_A)), [
                    Assign(ArrayRef(SymbolRef("A"), SymbolRef("i")),
                           FunctionCall(SymbolRef(apply_one.name),
                                        [ArrayRef(SymbolRef("A"), SymbolRef("i"))])),
                ], []),
            ]
        ).set_kernel()

        kernel = OclFile("kernel", [apply_one, apply_kernel])

        control = StringTemplate(r"""
        #ifdef __APPLE__
        #include <OpenCL/opencl.h>
        #else
        #include <CL/cl.h>
        #endif
        void apply_all(cl_command_queue queue, cl_kernel kernel, cl_mem buf) {
            size_t global = $n;
            size_t local = 32;
            clSetKernelArg(kernel, 0, sizeof(cl_mem), &buf);
            clEnqueueNDRangeKernel(queue, kernel, 1, NULL, &global, &local, 0, NULL, NULL);

        }
        """, {'n': Constant(len_A + 32 - (len_A % 32))})
        cfile = CFile("generated", [control], config_target='opencl')
        return kernel, cfile

    def finalize(self, transform_result, program_config):
        kernel, cfile = transform_result
        proj = Project([kernel, cfile])
        fn = OpFunction()

        program = cl.clCreateProgramWithSource(fn.context, kernel.codegen()).build()
        apply_kernel_ptr = program['apply_kernel']

        entry_type = ct.CFUNCTYPE(None, cl.cl_command_queue, cl.cl_kernel, cl.cl_mem)
        return fn.finalize(apply_kernel_ptr, proj, "apply_all", entry_type)

    def interpret(self, A):
        return np.vectorize(self.apply)(A)


# ---------------------------------------------------------------------------
# user code


def double(x):
    return x * 2


def square(x):
    return x * x


def main():
    doubler = OpTranslator.from_function(double, 'Doubler')
    squarer = OpTranslator.from_function(square, 'Squarer')

    data = np.arange(123, dtype=np.float32)

    # squaring floats
    actual   = squarer(data)
    expected = np.vectorize(square)(data)
    np.testing.assert_array_equal(actual, expected)
    print("Squarer works.")

    # doubling floats
    actual = doubler(data)
    expected = np.vectorize(double)(data)
    np.testing.assert_array_equal(actual, expected)
    print("Doubler works.")

if __name__ == '__main__':
    # Testing conventional (non-lambda) kernel function implementation
    main()

    # Testing lambda kernel function implementation
    double = lambda x: x * 2
    square = lambda x: x * x
    main()

