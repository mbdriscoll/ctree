__author__ = 'nzhang-dev'

from ctree.frontend import *; from ctree.c.nodes import MultiNode; from ctree.transformations import PyBasicConversions, DeclarationFiller
import unittest

def fib(n):
    a, b = 0, 1
    k = "hello"
    while n > 0:
        a, b = b, a + b
        n -= 1
    return a


class DeclarationTest(unittest.TestCase):

    def test_fib(self):
        py_ast = get_ast(fib).body[0]
        c_ast = PyBasicConversions().visit(py_ast)
        filled_ast = DeclarationFiller().visit(c_ast)