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
      PyCtypesToCtreeTypes(),
      PyBasicConversions(),
      FixUpParentPointers(),
    ]
    for tx in transformations:
      tree = tx.visit(tree)
    tree.return_type = tree.params[0].type
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
