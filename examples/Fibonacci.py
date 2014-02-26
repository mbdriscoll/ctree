"""
Builds an AST that computes the nth Fibonacci number.

In python:

  def fib(n):
    if n < 2:
      return n
    else:
      return fib(n-1) + fib(n-2)
"""

import ctypes as ct
from ctree.nodes.c import *

fib_ast = \
FunctionDecl(ct.c_int, "fib", [Param(ct.c_int, SymbolRef("n"))], [
  If(Lt(SymbolRef("n"), Constant(2)), \
    [Return(SymbolRef("n"))], \
    [Return(Add(FunctionCall(SymbolRef("fib"), [Sub(SymbolRef("n"), Constant(1))]), \
                FunctionCall(SymbolRef("fib"), [Sub(SymbolRef("n"), Constant(2))])))])
])

def main():
  print("Generated code is:\n%s" % fib_ast)

if __name__ == '__main__':
  main()
