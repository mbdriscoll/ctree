"""
Parses the python AST, transforms it to C, JITs it, and runs it.
"""

import ast
import inspect

from ctree.nodes import *
from ctree.dotgen import to_dot
from ctree.transformations import *
from ctree.analysis import VerifyAllCAstNodes
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
  intermediate_ast = frontend.get_ast(fib)

  transformations = [
    PyTypeRecognizer(),
    PyCtxScrubber(),
    PyBasicConversions(),
    FixUpParentPointers(),
  ]

  for tx in transformations:
    intermediate_ast = tx.visit(intermediate_ast)

  VerifyAllCAstNodes().visit(intermediate_ast)

  #print ("C program:\n%s" % intermediate_ast)
  #print (to_dot(intermediate_ast))

  mod = JitModule()
  mod.load(intermediate_ast)
  func_decl = intermediate_ast.body[0] # FIXME make ast lookup routines
  c_fib = mod.get_callable(func_decl)

  for i in range(20):
    assert fib(i) == c_fib(i)

  log.info("Success.")

if __name__ == '__main__':
  main()
