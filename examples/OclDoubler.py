"""
Parses the python AST below, transforms it to C, JITs it, and runs it.
"""

import logging

logging.basicConfig(level=20)

import numpy as np

from ctree.c.nodes import *
from ctree.c.types import *
from ctree.cpp.nodes import *
from ctree.ocl.nodes import *
from ctree.ocl.types import *
from ctree.ocl.macros import *
from ctree.transformations import *
from ctree.jit import LazySpecializedFunction
from ctree.types import get_ctree_type
from ctree.dotgen import to_dot

# ---------------------------------------------------------------------------
# Specializer code


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
        apply_one_typesig = [A_type.get_base_type(),
                             A_type.get_base_type()]
        apply_one.set_typesig(apply_one_typesig)

        apply_kernel = FunctionDecl(Void(), "apply_kernel",
                                    params=[SymbolRef("A", A_type), SymbolRef("n", Int())],
                                    defn=[
                                        Assign(SymbolRef("i", Int()),
                                               FunctionCall(SymbolRef("get_global_id"), [Constant(0)])),
                                        If(Lt(SymbolRef("i"), SymbolRef("n")), [
                                            Assign(ArrayRef(SymbolRef("A"), SymbolRef("i")),
                                                   FunctionCall(SymbolRef("apply"),
                                                                [ArrayRef(SymbolRef("A"), SymbolRef("i"))]))
                                        ])
                                    ])
        apply_kernel.set_kernel()

        kernel = OclFile("kernel", [apply_one, apply_kernel])
        kernel_path_ref = kernel.get_generated_path_ref()

        device_id = SymbolRef("device_id", cl_device_id())
        context = SymbolRef("context", cl_context())
        commands = SymbolRef("commands", cl_command_queue())
        kernel_source = SymbolRef("kernel_source", Ptr(Char()))
        kernel_path = SymbolRef("kernel_path", Ptr(Char()))

        control = CFile("control", [
            CppInclude("stdio.h"),
            CppInclude("OpenCL/opencl.h"),
            Assign(kernel_path.copy(declare=True), kernel_path_ref),
            FunctionDecl(Void(), "apply_all",
                         params=[SymbolRef("A", A_type)],
                         defn=[
                             device_id.copy(declare=True),
                             safe_clGetDeviceIDs(device_id=Ref(device_id.copy())),

                             context.copy(declare=True),
                             safe_clCreateContext(context.copy(), devices=Ref(device_id.copy())),

                             commands.copy(declare=True),
                             safe_clCreateCommandQueue(commands.copy(), context.copy(), device_id.copy()),

                             kernel_source.copy(declare=True),
                             read_program_into_string(kernel_source, kernel_path),
                             Return(),
                         ]
            ),
        ])
        tree = Project([kernel, control])
        return tree


class ArrayOp(object):
    """
    A class for managing independent operation on elements
    in numpy arrays.
    """

    def __init__(self):
        """Instantiate translator."""
        from ctree.frontend import get_ast

        self.c_apply_all = OpTranslator(get_ast(self.apply), "apply_all")

    def __call__(self, A):
        """Apply the operator to the arguments via a generated function."""
        return self.c_apply_all(A)


# ---------------------------------------------------------------------------
# User code

class Doubler(ArrayOp):
    """Double elements of the array."""

    def apply(x):
        return x * 2


def py_doubler(A):
    for i in range(len(A)):
        A[i] *= 2


def main():
    c_doubler = Doubler()

    # doubling doubles
    actual_d = np.ones(12, dtype=np.float64)
    expected_d = np.ones(12, dtype=np.float64)
    c_doubler(actual_d)
    py_doubler(expected_d)
    np.testing.assert_array_equal(actual_d, expected_d)

    print("Success.")


if __name__ == '__main__':
    main()
