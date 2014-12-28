"""
Parses the python AST below, transforms it to C, JITs it, and runs it.
"""

import logging

#logging.basicConfig(level=10)

import numpy as np

import ctypes as ct
from ctypes import *

import ctree.np

from ctree.frontend import get_ast
from ctree.c.nodes import *
from ctree.transformations import *
from ctree.jit import LazySpecializedFunction
from ctree.jit import ConcreteSpecializedFunction
from ctree.types import get_ctype
# from ctypes import CFUNCTYPE

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

        c_doubler = CFile("generated", [tree])
        return [c_doubler]

    def finalize(self, transform_result, program_config):
        
        c_doubler = transform_result[0]
        proj = Project([c_doubler])

        arg_config, tuner_config = program_config
        array_type = arg_config['ptr']
        entry_type = ct.CFUNCTYPE(None, array_type)
 
        concrete_Fn = ArrayFn()
        return concrete_Fn.finalize("apply_all", proj, entry_type)

class ArrayFn(ConcreteSpecializedFunction):
    def finalize(self, entry_point_name, project_node, entry_typesig):
        self._c_function = self._compile(entry_point_name, project_node, entry_typesig)
        return self

    def __call__(self, A):
        return self._c_function(A)

# ---------------------------------------------------------------------------
# User code

def double(n):
    return n * 2

def py_doubler(A):
    A *= 2

def main():

    # create a class called Doubler that has the function double(n) as an @staticmethod
    Doubler = OpTranslator.from_function(double, "Doubler")
    
    # creating instance of c_doubler()
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
