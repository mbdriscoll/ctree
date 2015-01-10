__author__ = 'nzhang-dev'

import ast

from ctree.transformations import DeclarationFiller, PyBasicConversions
from ctree.frontend import *
from ctree.c.nodes import MultiNode


code = [
    "a = 1",
    "a,b = 1,1",
    "a = b = 1",
    """a,b = 1,1 \na,b = b,a"""
]

def fib(n):
    a,b = 0, 1
    while n > 0:
        n -= 1
        a, b = b, a+b
    return a

asts = []
for c in code:
    parsed = ast.parse(c)
    asts.append(MultiNode(body = parsed.body))

asts.append(get_ast(fib).body[0])

processed = [
    DeclarationFiller().visit(PyBasicConversions().visit(a)) for a in asts
]