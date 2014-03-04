"""
Parses the python AST below, transforms it to C, JITs it, and runs it.
"""

import logging
logging.basicConfig(level=20)

import os
import numpy as np
import ctypes as ct
from __future__ import print_function

from ctree.frontend import get_ast
from ctree.c.nodes import *
from ctree.cpp.nodes import *
from ctree.ocl.nodes import *
from ctree.dotgen import to_dot
from ctree.transformations import *
from ctree.jit import LazySpecializedFunction
from ctree.types import pytype_to_ctype, get_ctype

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
    return (len(A), A.dtype, A.ndim, A.shape)

  def transform(self, py_ast, program_config):
    """
    Convert the Python AST to a C AST according to the directions
    given in program_config.
    """
    len_A, A_dtype, A_ndim, A_shape = program_config[0]
    inner_type = pytype_to_ctype(A_dtype)

    apply_one = PyBasicConversions().visit(py_ast.body[0])
    apply_one_typesig = [inner_type, inner_type]
    apply_one.set_typesig(apply_one_typesig)

    apply_all = FunctionDecl(None, "apply_all",
      params=[SymbolRef("A", ct.POINTER(inner_type)), SymbolRef("n", ct.c_int)],
      defn=[
        Assign(SymbolRef("i", ct.c_int), FunctionCall(SymbolRef("get_global_id"), [Constant(0)])),
        If(Lt(SymbolRef("i"), SymbolRef("n")), [
          Assign(ArrayRef(SymbolRef("A"), SymbolRef("i")),
                 FunctionCall(SymbolRef("apply"), [ArrayRef(SymbolRef("A"), SymbolRef("i"))]))
        ])
      ])
    apply_all.set_kernel()

    kernel = OclFile("kernel", [apply_one, apply_all])
    kernel_path_ref = kernel.get_generated_path_ref()

    control = CFile("control", [
      CppInclude("OpenCL/opencl.h"),
      Assign(SymbolRef("kernel_path", ct.c_char_p), kernel_path_ref),
      FunctionDecl(None, "apply_all",
        params=[SymbolRef("A")],
        defn=[ Return() ]
      ),
    ])

    tree = Project([kernel, control])

    transformations = [
      ConvertNumpyNdpointers(),
      StripPythonDocstrings(),
    ]
    for xf in transformations:
      tree = xf.visit(tree)

    return tree


class ArrayOp(object):
  """
  A class for managing independent operation on elements
  in numpy arrays.
  """
  def __init__(self):
    """Instantiate translator."""
    self.c_apply_all = OpTranslator(get_ast(self.apply), "apply_all")

  def __call__(self, A):
    """Apply the operator to the arguments via a generated function."""
    return self.c_apply_all(A)


# ---------------------------------------------------------------------------
# User code

class Doubler(ArrayOp):
  """Double elements of the array."""
  def apply(x):
    return x*2

def py_doubler(A):
  for i in xrange(len(A)):
    A[i] *= 2

def main():
  c_doubler = Doubler()

  # doubling doubles
  actual_d   = np.ones(12, dtype=np.float64)
  expected_d = np.ones(12, dtype=np.float64)
  c_doubler(actual_d)
  py_doubler(expected_d)
  np.testing.assert_array_equal(actual_d, expected_d)

  print("Success.")


if __name__ == '__main__':
  main()
