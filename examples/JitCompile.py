"""
Compiles and runs the AST defined in the Fibonacci example.
"""

from ctree.jit import Module
from ctree.nodes import FunctionDecl

from Fibonacci import fib_ast

def main():
  module = Module()
  module.compile(fib_ast)

  fib_fn = fib_ast.body[0]
  assert isinstance(fib_fn, FunctionDecl)

  c_fib = module.get_callable(fib_fn)

  print("Evaluating:")
  for i in range(20):
    print("fib(%2d) = %d" % (i, c_fib(i)))

if __name__ == '__main__':
  main()
