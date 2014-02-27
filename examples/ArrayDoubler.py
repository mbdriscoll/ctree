"""
Parses the python AST below, transforms it to C, JITs it, and runs it.
"""

import numpy as np
import ctypes as ct

from ctree.frontend import get_ast
from ctree.nodes import *
from ctree.dotgen import to_dot
from ctree.transformations import *
from ctree.analyses import VerifyOnlyCAstNodes
from ctree.jit import LazySpecializedFunction

import logging
logging.basicConfig(level=20)

# ---------------------------------------------------------------------------
# Specializer library

class OpTranslator(LazySpecializedFunction):
  _NUMPY_DTYPE_TO_CTYPE = {
    np.dtype('float64'): ct.c_double,
    # TODO add the rest
  }

  @staticmethod
  def _numpy_dtype_to_ctype(dtype):
    try:
      return OpTranslator._NUMPY_DTYPE_TO_CTYPE[dtype]
    except KeyError:
      raise Exception("Cannot convertion Numpy dtype '%s' to ctype." % dtype)

  def transform(self, tree, args):
    """Convert the Python AST to a C AST."""
    len_A, A = args
    array_type = np.ctypeslib.ndpointer(dtype=A.dtype, ndim=A.ndim, shape=A.shape, flags=A.flags)
    apply_all_typesig = [ct.c_void_p, ct.c_int, array_type]

    inner_type = self._numpy_dtype_to_ctype(A.dtype)
    apply_one_typesig = [inner_type, inner_type]

    transformations = [
      SetParamTypes("apply_all", apply_all_typesig),
      SetParamTypes("apply",     apply_one_typesig),
      ConvertNumpyNdpointers(),
      StripPythonDocstrings(),
      PyBasicConversions(),
      FixUpParentPointers(),
    ]

    for nth, tx in enumerate(transformations):
      with open("graph.%d.dot" % nth, 'w') as ofile:
        ofile.write( to_dot(tree) )
      tree = tx.visit(tree)
    with open("graph.%d.dot" % (nth+1), 'w') as ofile:
      ofile.write( to_dot(tree) )

    tree.return_type = ctypes.c_void_p
    return tree


class ArrayOp(object):
  """
  A class for managing independent operation on elements
  in numpy arrays.
  """
  def __init__(self):
    """Instantiate translator."""
    kernel = get_ast(self.apply).body[0]
    control = FunctionDecl(ct.c_void_p, "apply_all",
      params=[SymbolRef("len_A", ct.c_size_t), SymbolRef("A")],
      defn=[
        For(Assign(SymbolRef("i", ct.c_int), Constant(0)),
            Lt(SymbolRef("i"), SymbolRef("len_A")),
            PostInc(SymbolRef("i")),
            [
              Assign(ArrayRef(SymbolRef("A"),SymbolRef("i")),
                     FunctionCall(SymbolRef("apply"), [ArrayRef(SymbolRef("A"),SymbolRef("i"))])),
            ]),
      ]
    )
    project = File([kernel, control])
    self.c_apply_all = OpTranslator(project, "apply_all")

  def __call__(self, A):
    """Apply the operator to the arguments."""
    return self.c_apply_all(len(A), A)


# ---------------------------------------------------------------------------
# User-defined code

class Doubler(ArrayOp):
  def apply(n):
    """Double one element of the array."""
    return n*2


def main():
  c_doubler = Doubler()

  actual   = np.ones(12, dtype=np.double)
  expected = np.ones(12, dtype=np.double)

  c_doubler(actual)
  doubler(expected)

  np.testing.assert_array_equal(actual, expected)
  print("Success.")


if __name__ == '__main__':
  main()
