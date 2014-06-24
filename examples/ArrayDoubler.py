"""
Parses the python AST below, transforms it to C, JITs it, and runs it.
"""

import logging

#logging.basicConfig(level=10)

import numpy as np

from ctypes import *
import ctree.np

from ctree.frontend import get_ast
from ctree.c.nodes import *
from ctree.transformations import *
from ctree.jit import LazySpecializedFunction
from ctree.jit import ConcreteSpecializedFunction
from ctree.types import get_ctype

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
        return {
            'ptr': np.ctypeslib.ndpointer(A.dtype, A.ndim, A.shape),
        }

    def transform(self, py_ast, program_config):
        """
        Convert the Python AST to a C AST according to the directions
        given in program_config.
        """
        arg_config, tuner_config = program_config
        array_type = arg_config['ptr']
        nItems = np.prod(array_type._shape_)
        inner_type = array_type._dtype_.type()

        tree = CFile("generated", [
            py_ast.body[0],
            FunctionDecl(None, "apply_all",
                         params=[SymbolRef("A", array_type())],
                         defn=[
                             For(Assign(SymbolRef("i", c_int()), Constant(0)),
                                 Lt(SymbolRef("i"), Constant(nItems)),
                                 PostInc(SymbolRef("i")),
                                 [
                                     Assign(ArrayRef(SymbolRef("A"), SymbolRef("i")),
                                            FunctionCall(SymbolRef("apply"), [ArrayRef(SymbolRef("A"),
                                                                                       SymbolRef("i"))])),
                                 ]),
                         ]
            ),
        ])

        tree = PyBasicConversions().visit(tree)

        apply_one = tree.find(FunctionDecl, name="apply")
        apply_one.set_static().set_inline()
        apply_one.return_type = inner_type
        apply_one.params[0].type = inner_type

        entry_point_typesig = tree.find(FunctionDecl, name="apply_all").get_type()
        print "FUNCTYPE", entry_point_typesig._restype_, entry_point_typesig._argtypes_

        proj = Project([tree])
        return ArrayFn().finalize("apply_all", proj, entry_point_typesig)

class ArrayFn(ConcreteSpecializedFunction):
    def finalize(self, entry_point_name, project_node, entry_typesig):
        self._c_function = self._compile(entry_point_name, project_node, entry_typesig)
        return self

    def __call__(self, A):
        return self._c_function(A)

class ArrayOp(object):
    """
    A class for managing independent operation on elements
    in numpy arrays.
    """

    def __init__(self):
        """Instantiate translator."""
        self.c_apply_all = OpTranslator(get_ast(self.apply))

    def __call__(self, A):
        """Apply the operator to the arguments via a generated function."""
        return self.c_apply_all(A)


# ---------------------------------------------------------------------------
# User code

class Doubler(ArrayOp):
    """Double elements of the array."""

    def apply(n):
        return n * 2


def py_doubler(A):
    A *= 2


def main():
    c_doubler = Doubler()

    # doubling doubles
    actual_d = np.ones(12, dtype=np.float64)
    expected_d = np.ones(12, dtype=np.float64)
    c_doubler(actual_d)
    py_doubler(expected_d)
    np.testing.assert_array_equal(actual_d, expected_d)

    # doubling floats
    actual_f = np.ones(13, dtype=np.float32)
    expected_f = np.ones(13, dtype=np.float32)
    c_doubler(actual_f)
    py_doubler(expected_f)
    np.testing.assert_array_equal(actual_f, expected_f)

    # doubling ints
    actual_i = np.ones(14, dtype=np.int32)
    expected_i = np.ones(14, dtype=np.int32)
    c_doubler(actual_i)
    py_doubler(expected_i)
    np.testing.assert_array_equal(actual_i, expected_i)

    # demonstrate caching
    c_doubler(actual_i)
    c_doubler(actual_i)
    py_doubler(expected_i)
    py_doubler(expected_i)
    np.testing.assert_array_equal(actual_i, expected_i)

    print("Success.")


if __name__ == '__main__':
    main()
