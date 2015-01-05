import unittest
from inspect import getsource

from ctree.frontend import *
from fixtures.sample_asts import *


class TestFrontend(unittest.TestCase):
    def test_identity(self):
        self.assertIsInstance(get_ast(identity), ast.AST)

    def test_gcd(self):
        self.assertIsInstance(get_ast(gcd), ast.AST)

    def test_fib(self):
        self.assertIsInstance(get_ast(fib), ast.AST)

    def test_parse_print(self):
        parseprint(getsource(fib))

    def test_dump(self):
        dump(fib_ast)
        #self.assertEqual(dump(fib_ast), 'FunctionDecl(params=[\n    SymbolRef(),\n  ], defn=[\n    If(cond=BinaryOp(left=SymbolRef(), right=Constant()), then=[\n        Return(value=SymbolRef()),\n      ], elze=[\n        Return(value=BinaryOp(left=FunctionCall(func=SymbolRef(), args=[\n            BinaryOp(left=SymbolRef(), right=Constant()),\n          ]), right=FunctionCall(func=SymbolRef(), args=[\n            BinaryOp(left=SymbolRef(), right=Constant()),\n          ]))),\n      ]),\n  ])')