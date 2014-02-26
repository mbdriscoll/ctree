"""
Parses the python AST below, transforms it to C, JITs it, and runs it.
"""

import numpy as np

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
  def transform(self, tree):
    """Convert the Python AST to a C AST."""
    transformations = [
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
    self.c_apply = OpTranslator( get_ast(self.apply) )

  def __call__(self, *args, **kwargs):
    """Apply the operator to the arguments."""
    return self.c_apply(*args, **kwargs)


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
