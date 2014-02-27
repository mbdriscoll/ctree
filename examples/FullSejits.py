"""
Parses the python AST below, transforms it to C, JITs it, and runs it.
"""

import logging
logging.basicConfig(level=20)

import numpy as np

from ctree.transformations import *
from ctree.frontend import get_ast
from ctree.jit import LazySpecializedFunction

def fib(n):
  if n < 2:
    return n
  else:
    return fib(n-1) + fib(n-2)


class BasicTranslator(LazySpecializedFunction):
  def __init__(self, func):
    super().__init__( get_ast(func), func.__name__ )

  def transform(self, tree, args):
    """Convert the Python AST to a C AST."""
    fib_arg_type = pytype_to_ctype( type(args[0]) )
    fib_sig = (fib_arg_type, fib_arg_type)

    from ctree.dotgen import to_dot
    with open("graph.dot", 'w') as ofile:
      ofile.write( to_dot(tree) )

    transformations = [
      PyBasicConversions(),
      FixUpParentPointers(),
      SetParamTypes("fib", fib_sig),
    ]
    for tx in transformations:
      tree = tx.visit(tree)

    return tree


def main():
  c_fib = BasicTranslator(fib)

  assert fib(10) == c_fib(10)
  assert fib(11) == c_fib(11)
  assert fib(12) == c_fib(12)
  assert fib(13) == c_fib(13)

  assert fib(13.3) == c_fib(13.3)
  assert fib(13.4) == c_fib(13.4)
  assert fib(13.5) == c_fib(13.5)
  assert fib(13.6) == c_fib(13.6)

  assert fib(14) == c_fib(14)
  assert fib(13.7) == c_fib(13.7)

  print("Success.")


if __name__ == '__main__':
  main()
