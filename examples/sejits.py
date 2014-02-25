"""
Parses the python AST below, transforms it to C, JITs it, and runs it.
"""

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
  my_ast = frontend.get_ast(fib)

  transformations = [
    PyTypeRecognizer(),
    PyBasicConversions(),
    FixUpParentPointers(),
  ]

  for nth, tx in enumerate(transformations):
    with open("graph.%s.dot" % nth, 'w') as ofile:
      print(to_dot(my_ast), file=ofile)
    my_ast = tx.visit(my_ast)

  with open("graph.%s.dot" % (nth+1), 'w') as ofile:
    print(to_dot(my_ast), file=ofile)

  VerifyAllCAstNodes().visit(my_ast)

  mod = JitModule()
  mod.load(my_ast)
  func_decls = my_ast.find_all(
    lambda n: type(n) == FunctionDecl and n.name.name == "fib")
  c_fib = mod.get_callable(next(func_decls))

  for i in range(20):
    assert fib(i) == c_fib(i)

  log.info("Success.")

if __name__ == '__main__':
  main()
