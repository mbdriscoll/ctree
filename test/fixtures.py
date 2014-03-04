"""
A collection of pre-built ASTs for use in testing.
"""

from ctree.c.nodes import *
from ctree.c.types import *

# ---------------------------------------------------------------------------
# integer identity

def identity(x):
  return x

identity_ast = \
FunctionDecl(Int(), "identity", [SymbolRef(SymbolRef("x"), Int())], [
  Return(SymbolRef("x"))
])


# ---------------------------------------------------------------------------
# greatest common divisor

def gcd(a, b):
  if b == 0:
    return a
  else:
    return gcd(b, a % b)

gcd_ast = \
FunctionDecl(Int(), "gcd", [SymbolRef("a", Int()), SymbolRef("b", Int())], [
  If(Eq(SymbolRef('b'),Constant(0)), \
    [Return(SymbolRef('a'))], \
    [Return(FunctionCall(SymbolRef('gcd'), [SymbolRef('b'), Mod(SymbolRef('a'), \
                                                                SymbolRef('b'))]))])
])


# ---------------------------------------------------------------------------
# naive fibonacci

def fib(n):
  if n < 2:
    return n
  else:
    return fib(n-1) + fib(n-2)

fib_ast = \
FunctionDecl(Int(), "fib", [SymbolRef("n", Int())], [
  If(Lt(SymbolRef("n"), Constant(2)), \
    [Return(SymbolRef("n"))], \
    [Return(Add(FunctionCall(SymbolRef("fib"), [Sub(SymbolRef("n"), Constant(1))]), \
                FunctionCall(SymbolRef("fib"), [Sub(SymbolRef("n"), Constant(2))])))])
])


# ---------------------------------------------------------------------------
# a zero-argument function

def get_two():
  return 2

get_two_ast = \
FunctionDecl(Long(), "get_two", [], [
  Return(Constant(2))
])


# ---------------------------------------------------------------------------
# a function with mixed argument types

def choose(p, a, b):
  if p < 0.5:
    return a
  else:
    return b

choose_ast = \
FunctionDecl(Long(), "choose",
  [SymbolRef("p", Double()), SymbolRef("a", Long()), SymbolRef("b", Long())], [
  If(Lt(SymbolRef("p"), Constant(0.5)), [
    Return(SymbolRef("a")),
  ], [
    Return(SymbolRef("b")),
  ])
])
