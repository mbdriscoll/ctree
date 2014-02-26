"""
Parses the python AST below, transforms it to C, JITs it, and runs it.
"""

import ast

from ctree.frontend import get_ast
from ctree.nodes import *
from ctree.dotgen import to_dot
from ctree.transformations import *
from ctree.analyses import VerifyOnlyCAstNodes
from ctree.jit import LazySpecializedFunction

import numpy as np

import logging
logging.basicConfig(level=20)
log = logging.getLogger(__name__)

class SimpleTranslator(LazySpecializedFunction):
  def transform(self, tree):
    transformations = [
      PyCtypesToCtreeTypes(),
      PyBasicConversions(),
      FixUpParentPointers(),
    ]
    for tx in transformations:
      tree = tx.visit(tree)
    tree.return_type = tree.params[0].type # hack until type inference works
    return tree

def fib(n):
  if n < 2:
    return n
  else:
    return fib(n-1) + fib(n-2)

def main():
  py_ast = get_ast(fib).body[0]
  c_fib = SimpleTranslator(py_ast)

  print( c_fib(10) )
  print( c_fib(11) )
  print( c_fib(12) )
  print( c_fib(13) )

  """
  actual   = np.ones(10, dtype=np.float32)
  expected = np.ones(10, dtype=np.float32)

  c_doubler(actual)
  doubler(expected)

  np.testing.assert_array_equal(actual, expected)
  """
  log.info("Success.")

if __name__ == '__main__':
  main()
