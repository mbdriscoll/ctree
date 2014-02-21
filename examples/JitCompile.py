"""
Compiles and runs the AST defined in the Fibonacci example.
"""

import logging
logging.basicConfig(level=20) # print INFO messages

from ctree.jit import Module
from ctree.nodes import *

fib_ast = File([
  FunctionDecl(Int(), SymbolRef("fib"), [Param(Int(), SymbolRef("n"))], [
    If(Lt(SymbolRef("n"), Constant(2)), \
      [Return(SymbolRef("n"))], \
      [Return(Add(FunctionCall(SymbolRef("fib"), [Sub(SymbolRef("n"), Constant(1))]), \
                  FunctionCall(SymbolRef("fib"), [Sub(SymbolRef("n"), Constant(2))])))])
  ])
])


def main():
  module = Module()
  module.load(fib_ast)

  fib_fn = fib_ast.body[0]
  assert isinstance(fib_fn, FunctionDecl)

  c_fib = module.get_callable(fib_fn)

  print("Evaluating:")
  for i in range(20):
    print("fib(%2d) = %d" % (i, c_fib(i)))

if __name__ == '__main__':
  main()
