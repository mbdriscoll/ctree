__author__ = 'nzhang-dev'

from ctree.transformations import DeclarationFiller, PyBasicConversions
from ctree.frontend import *
import ast
from ctree.c.nodes import MultiNode

code = [
    "a = 1",
    "a,b = 1,1",
    "a = b = 1",
    """a,b = 1,1 \na,b = b,a"""
]

asts = []
for c in code:
    parsed = ast.parse(c)
    asts.append(MultiNode(body = parsed.body))

processed = [
    DeclarationFiller().visit(PyBasicConversions().visit(a)) for a in asts
]