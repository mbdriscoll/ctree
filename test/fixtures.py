"""
A collection of pre-built ASTs for use in testing.
"""

import ctypes as ct
from ctree.nodes.c import *

# ---------------------------------------------------------------------------
# integer identity

def identity(x :int) -> int:
  return x

identity_ast = \
FunctionDecl(ct.c_int, "identity", [SymbolRef(SymbolRef("x"), ct.c_int)], [
  Return(SymbolRef("x"))
])

# ---------------------------------------------------------------------------
# greatest common divisor

def gcd(a :int, b :int) -> int:
  if b == 0:
    return a
  else:
    return gcd(b, a % b)

gcd_ast = \
FunctionDecl(ct.c_int, "gcd", [SymbolRef("a", ct.c_int), SymbolRef("b", ct.c_int)], [
  If(Eq(SymbolRef('b'),Constant(0)), \
    [Return(SymbolRef('a'))], \
    [Return(FunctionCall(SymbolRef('gcd'), [SymbolRef('b'), Mod(SymbolRef('a'), \
                                                                SymbolRef('b'))]))])
])

# ---------------------------------------------------------------------------
# naive fibonacci

def fib(n :int) -> int:
  if n < 2:
    return n
  else:
    return fib(n-1) + fib(n-2)

fib_ast = \
FunctionDecl(ct.c_int, "fib", [SymbolRef("n", ct.c_int)], [
  If(Lt(SymbolRef("n"), Constant(2)), \
    [Return(SymbolRef("n"))], \
    [Return(Add(FunctionCall(SymbolRef("fib"), [Sub(SymbolRef("n"), Constant(1))]), \
                FunctionCall(SymbolRef("fib"), [Sub(SymbolRef("n"), Constant(2))])))])
])
