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
from ctree.templates.nodes import FileTemplate
from ctree.transformations import *
from ctree.jit import LazySpecializedFunction
from ctree.types import get_ctree_type

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
        apply_one_typesig = FuncType(A_type.get_base_type(), [A_type.get_base_type()])
        apply_one.set_typesig(apply_one_typesig)

        apply_kernel = FunctionDecl(Void(), "apply_kernel",
                                    params=[SymbolRef("A", A_type)],
                                    defn=[
                                        Assign(SymbolRef("i", Int()),
                                               FunctionCall(SymbolRef("get_global_id"), [Constant(0)])),
                                        If(Lt(SymbolRef("i"), Constant(len_A)), [
                                            Assign(ArrayRef(SymbolRef("A"), SymbolRef("i")),
                                                   FunctionCall(SymbolRef("apply"),
                                                                [ArrayRef(SymbolRef("A"), SymbolRef("i"))]))
                                        ])
                                    ])

        # add opencl type qualifiers
        apply_kernel.set_kernel()
        apply_kernel.params[0].set_global()

        kernel = OclFile("kernel", [apply_one, apply_kernel])

        template_args = {
            'array_decl': SymbolRef("data", A_type),
            'array_ref':  SymbolRef("data"),
            'count':      Constant(len_A),
            'kernel_path': kernel.get_generated_path_ref(),
            'kernel_name': String(apply_kernel.name),
        }
        template_path = os.path.join(os.getcwd(), "templates", "OclDoubler.tmpl.c")

        control = CFile("control", [
            FileTemplate(template_path, template_args),
        ])
        tree = Project([kernel, control])

        with open("graph.dot", 'w') as f:
          f.write( tree.to_dot() )

        entry_point_typesig = FuncType(Int(), [A_type]).as_ctype()
        return tree, entry_point_typesig


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
        retval = self.c_apply_all(A)
        assert retval == 0, "Specialized function exited with non-zero value: %d" % retval


# ---------------------------------------------------------------------------
# User code

class Doubler(ArrayOp):
    """Double elements of the array."""

    def apply(x):
        return x * 2


class Squarer(ArrayOp):
    """Double elements of the array."""

    def apply(x):
        return x * x


def py_doubler(A):
    for i in range(len(A)):
        A[i] *= 2

def py_squarer(A):
    for i in range(len(A)):
        A[i] *= A[i]

def main():
    # squaring floats
    c_squarer = Squarer()
    actual_d = np.ones(1024, dtype=np.float32)
    expected_d = np.ones(1024, dtype=np.float32)
    c_squarer(actual_d)
    py_squarer(expected_d)
    np.testing.assert_array_equal(actual_d, expected_d)
    print("Squarer works.")

    # doubling floats
    c_doubler = Doubler()
    actual_d = np.ones(1024, dtype=np.float32)
    expected_d = np.ones(1024, dtype=np.float32)
    c_doubler(actual_d)
    py_doubler(expected_d)
    np.testing.assert_array_equal(actual_d, expected_d)
    print("Doubler works.")


if __name__ == '__main__':
    main()
