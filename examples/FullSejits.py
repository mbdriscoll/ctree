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

def fib(n):
  if n < 2:
    return n
  else:
    return fib(n-1) + fib(n-2)


class BasicTranslator(LazySpecializedFunction):
  def __init__(self, func_obj):
    func_def_ast = get_ast(func_obj).body[0]
    super().__init__(func_def_ast)

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
