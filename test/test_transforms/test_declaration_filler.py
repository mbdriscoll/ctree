__author__ = 'nzhang-dev'

import unittest

from ctree.frontend import *;
from ctree.transformations import PyBasicConversions
from ctree.transforms import DeclarationFiller


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
        print(filled_ast)
        expected = """
void fib(n) {

    long a = 0;
    long b = 1;


    char* k = "hello";

    while (n > 0) {

        long ____temp__a = b;
        long ____temp__b = a + b;
        a = ____temp__a;
        b = ____temp__b;

        n -= 1;
    }
    return a;
}"""
        stripped_actual = str(filled_ast).replace(" ", "").replace("\n", "")
        stripped_expected = expected.replace(" ", "").replace("\n", "")
        self.assertEqual(stripped_actual, stripped_expected)

    def test_fmin(self):
        def func():
            a = 3.0
            b = 4.0
            c = fmax(a + b, 0.0)
            return c
        py_ast = get_ast(func).body[0]
        c_ast = PyBasicConversions().visit(py_ast)
        filled_ast = DeclarationFiller().visit(c_ast)
        expected = """
void func() {
    double a = 3.0;
    double b = 4.0;
    double ____temp__c = fmax(a + b, 0.0);
    double c = ____temp__c;
    return c;
}"""
        stripped_actual = str(filled_ast).replace(" ", "").replace("\n", "")
        stripped_expected = expected.replace(" ", "").replace("\n", "")
        self.assertEqual(stripped_actual, stripped_expected)
