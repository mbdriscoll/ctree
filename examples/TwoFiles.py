"""
Parses the python AST below, transforms it to C, JITs it, and runs it.
Similar to ArrayDoubler, but puts kernel and control functions in
separate C files.
"""

import logging
logging.basicConfig(level=20)

import numpy as np
import ctypes as ct

from ctree.frontend import get_ast
from ctree.c.nodes import *
from ctree.dotgen import to_dot
from ctree.transformations import *
from ctree.jit import LazySpecializedFunction
from ctree.types import pytype_to_ctype, get_ctype

# ---------------------------------------------------------------------------
# Specializer code

class OpTranslator(LazySpecializedFunction):
  def args_to_subconfig(self, args):
    A = args[0]
    return (len(A), A.dtype, A.ndim, A.shape)

  def transform(self, tree, program_config):
    """Convert the Python AST to a C AST."""
    len_A, A_dtype, A_ndim, A_shape = program_config[0]
    inner_type = pytype_to_ctype(A_dtype)

    array_type = np.ctypeslib.ndpointer(A_dtype, A_ndim, A_shape)
    apply_all_typesig = [None, array_type]
    apply_one_typesig = [inner_type, inner_type]

    transformations = [
      SetTypeSignature("apply_all", apply_all_typesig),
      SetTypeSignature("apply",     apply_one_typesig),
      ConvertNumpyNdpointers(),
      StripPythonDocstrings(),
      PyBasicConversions(),
      FixUpParentPointers(),
    ]

    for xf in transformations:
      tree = xf.visit(tree)

    tree.find(SymbolRef, name="len_A").replace(Constant(len_A))

    return tree


class ArrayOp(object):
  """
  A class for managing independent operation on elements
  in numpy arrays.
  """
  def __init__(self):
    """Instantiate translator."""
    kernel = CFile("kernel", [get_ast(self.apply).body[0]])
    control = CFile("control", [
     FunctionDecl(ct.c_void_p, "apply",
      params=[SymbolRef("x")],
      defn=[]
     ),
     FunctionDecl(ct.c_void_p, "apply_all",
      params=[SymbolRef("A")],
      defn=[
        For(Assign(SymbolRef("i", ct.c_int), Constant(0)),
            Lt(SymbolRef("i"), SymbolRef("len_A")),
            PostInc(SymbolRef("i")),
            [
              Assign(ArrayRef(SymbolRef("A"),SymbolRef("i")),
                     FunctionCall(SymbolRef("apply"), [ArrayRef(SymbolRef("A"),SymbolRef("i"))])),
            ])]
      ),
    ])
    project = Project([kernel, control])
    self.c_apply_all = OpTranslator(project, "apply_all")

  def __call__(self, A):
    """Apply the operator to the arguments via a generated function."""
    return self.c_apply_all(A)


# ---------------------------------------------------------------------------
# User code

class Doubler(ArrayOp):
  """Double elements of the array."""
  def apply(n):
    return n*2

def py_doubler(A):
  for i in range(len(A)):
    A[i] *= 2

def main():
  c_doubler = Doubler()

  # doubling doubles
  actual_d   = np.ones(12, dtype=np.float64)
  expected_d = np.ones(12, dtype=np.float64)
  c_doubler(actual_d)
  py_doubler(expected_d)
  np.testing.assert_array_equal(actual_d, expected_d)

  # doubling floats
  actual_f   = np.ones(13, dtype=np.float32)
  expected_f = np.ones(13, dtype=np.float32)
  c_doubler(actual_f)
  py_doubler(expected_f)
  np.testing.assert_array_equal(actual_f, expected_f)

  # doubling longs
  actual_i   = np.ones(14, dtype=np.int32)
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
