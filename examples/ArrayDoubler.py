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

def doubler(A):
  for i in range(len(A)):
    A[i] *= 2


class BasicTranslator(LazySpecializedFunction):
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


def main():
  c_doubler = BasicTranslator( get_ast(doubler) )

  actual   = np.ones(10, dtype=np.double)
  expected = np.ones(10, dtype=np.double)

  c_doubler(actual)
  doubler(expected)

  np.testing.assert_array_equal(actual, expected)
  print("Success.")


if __name__ == '__main__':
  main()
