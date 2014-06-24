"""
Builds an AST that computes the nth Fibonacci number.

In python:

  def fib(n):
    if n < 2:
      return n
    else:
      return fib(n-1) + fib(n-2)
"""

from ctypes import *
from ctree.c.nodes import *

fib_ast = \
    FunctionDecl(c_int(), "fib", [SymbolRef("n", c_int())], [
        If(Lt(SymbolRef("n"), Constant(2)),
           [Return(SymbolRef("n"))],
           [Return(Add(FunctionCall(SymbolRef("fib"), [Sub(SymbolRef("n"), Constant(1))]),
                       FunctionCall(SymbolRef("fib"), [Sub(SymbolRef("n"), Constant(2))])))])
    ])


def main():
    print ("Generated code is:\n%s" % fib_ast)


if __name__ == '__main__':
    main()
