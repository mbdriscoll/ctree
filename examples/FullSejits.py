"""
Parses the python AST below, transforms it to C, JITs it, and runs it.
"""

from ctree.nodes import *
from ctree.dotgen import to_dot
from ctree.transformations import *
from ctree.analyses import VerifyOnlyCAstNodes
from ctree.jit import JitModule

import logging
logging.basicConfig(level=20)
log = logging.getLogger(__name__)

# program to transform to C
def fib(n :int) -> int:
  if n < 2:
    return n
  else:
    return fib(n-1) + fib(n-2)

def main():
  import ctree.frontend as frontend
  my_ast = frontend.get_ast(fib)

  transformations = [
    PyTypeRecognizer(),
    PyBasicConversions(),
    FixUpParentPointers(),
  ]

  for tx in transformations:
    my_ast = tx.visit(my_ast)

  VerifyOnlyCAstNodes().visit(my_ast)

  mod = JitModule().load(my_ast)
  fib_decl = my_ast.find(FunctionDecl, name="fib")
  c_fib = mod.get_callable(fib_decl)

  for i in range(20):
    assert fib(i) == c_fib(i)

  log.info("Success.")

if __name__ == '__main__':
  main()
