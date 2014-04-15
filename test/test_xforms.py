import ast
import sys
import unittest

from fixtures.sample_asts import *
from ctree.transformations import *
from ctree.c.nodes import *
from ctree.c.types import *
from ctree.frontend import get_ast


class TestSetTypeSig(unittest.TestCase):
    def _check(self, func_type, tree):
        if isinstance(tree, FunctionDecl):
            self.assertEqual(tree.return_type, func_type.return_type)
            for param, expected_type in zip(tree.params, func_type.arg_types):
                self.assertEqual(param.type, expected_type)
        elif isinstance(tree, ast.Module):
            self._check(func_type, tree.body[0])
        else:
            self.fail("Can't check param setting on %s object." % tree)

    def test_no_args(self):
        func_type = FuncType(Long())
        get_two_ast.set_typesig(func_type)
        self._check(func_type, get_two_ast)

    def test_one_arg(self):
        func_type = FuncType(Long(), [Long()])
        fib_ast.set_typesig(func_type)
        self._check(func_type, fib_ast)

    def test_two_args(self):
        func_type = FuncType(Long(), [Long(), Long()])
        gcd_ast.set_typesig(func_type)
        self._check(func_type, gcd_ast)

    def test_mixed_args(self):
        func_type = FuncType(Long(), [Double(), Long(), Long()])
        choose_ast.set_typesig(func_type)
        self._check(func_type, choose_ast)


class TestCtxScrubber(unittest.TestCase):
    def _check(self, tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                self.assertIsNone(node.ctx)

    def test_identity(self):
        tree = PyCtxScrubber().visit(get_ast(identity))
        self._check(tree)

    def test_fib(self):
        tree = PyCtxScrubber().visit(get_ast(fib))
        self._check(tree)

    def test_gcd(self):
        tree = PyCtxScrubber().visit(get_ast(gcd))
        self._check(tree)


class TestStripDocstrings(unittest.TestCase):
    def foo(self):
        """my docstring"""
        pass

    class Bar():
        """my other docstring"""
        pass

    def _check(self, tree):
        for node in ast.walk(tree):
            self.assertNotIsInstance(node, ast.Str)

    def test_func_docstring(self):
        tree = PyBasicConversions().visit(get_ast(self.foo))
        self._check(tree)

    def test_class_docstring(self):
        tree = PyBasicConversions().visit(get_ast(self.Bar))
        self._check(tree)

    def test_subtree_docstrings(self):
        tree = PyBasicConversions().visit(ast.Module([
            get_ast(self.foo),
            get_ast(self.Bar),
        ]))
        self._check(tree)


class TestBasicConversions(unittest.TestCase):
    def _check(self, py_ast, expected_c_ast):
        actual_c_ast = PyBasicConversions().visit(py_ast)
        self.assertEqual(str(actual_c_ast), str(expected_c_ast))

    def test_num_float(self):
        py_ast = ast.Num(123.4)
        c_ast = Constant(123.4)
        self._check(py_ast, c_ast)

    def test_num_int(self):
        py_ast = ast.Num(123)
        c_ast = Constant(123)
        self._check(py_ast, c_ast)

    def test_str(self):
        py_ast = ast.Str("foo bar")
        c_ast = String("foo bar")
        self._check(py_ast, c_ast)

    def test_name(self):
        py_ast = ast.Name("baz", ast.Load())
        c_ast = SymbolRef("baz")
        self._check(py_ast, c_ast)

    def test_binop(self):
        py_ast = ast.BinOp(ast.Num(1), ast.Add(), ast.Num(2))
        c_ast = Add(Constant(1), Constant(2))
        self._check(py_ast, c_ast)

    def test_return(self):
        py_ast = ast.Return()
        c_ast = Return()
        self._check(py_ast, c_ast)

    def test_if_else(self):
        py_ast = ast.If(ast.Num(1), [ast.Num(2)], [ast.Num(3)])
        c_ast = If(Constant(1), [Constant(2)], [Constant(3)])
        self._check(py_ast, c_ast)

    def test_if(self):
        py_ast = ast.If(ast.Num(1), [ast.Num(2)], [])
        c_ast = If(Constant(1), [Constant(2)])
        self._check(py_ast, c_ast)

    def test_ifexp(self):
        py_ast = ast.IfExp(ast.Num(1), ast.Num(2), ast.Num(3))
        c_ast = TernaryOp(Constant(1), Constant(2), Constant(3))
        self._check(py_ast, c_ast)

    def test_compare(self):
        py_ast = ast.Compare(ast.Num(1), [ast.Lt()], [ast.Num(2)])
        c_ast = Lt(Constant(1), Constant(2))
        self._check(py_ast, c_ast)

    @unittest.skipIf(sys.version_info.major == 2, "arg not defined for python2")
    def test_arg(self):
        py_ast = ast.arg("foo", None)
        c_ast = SymbolRef("foo")
        self._check(py_ast, c_ast)

    def test_for_1_arg(self):
        stop = ast.Num(10)
        py_ast = ast.For(ast.Name("i", ast.Load()),
            ast.Call(ast.Name("range", ast.Load()), [stop], [], None, None),
            [ast.Name("foo", ast.Load())],
            [],
        )
        i = SymbolRef("i", Long())
        c_ast = For(
            Assign(i, Constant(0)),
            Lt(i.copy(), Constant(10)),
            AddAssign(i.copy(), Constant(1)),
            [SymbolRef("foo")],
        )
        self._check(py_ast, c_ast)

    def test_for_2_args(self):
        start = ast.Num(2)
        stop = ast.Num(10)
        py_ast = ast.For(ast.Name("i", ast.Load()),
            ast.Call(ast.Name("range", ast.Load()), [start, stop], [], None, None),
            [ast.Name("foo", ast.Load())],
            [],
        )
        i = SymbolRef("i", Long())
        c_ast = For(
            Assign(i, Constant(2)),
            Lt(i.copy(), Constant(10)),
            AddAssign(i.copy(), Constant(1)),
            [SymbolRef("foo")],
        )
        self._check(py_ast, c_ast)

    def test_for_3_args(self):
        start = ast.Num(2)
        stop = ast.Num(10)
        step = ast.Num(3)
        py_ast = ast.For(ast.Name("i", ast.Load()),
            ast.Call(ast.Name("range", ast.Load()), [start, stop, step], [], None, None),
            [ast.Name("foo", ast.Load())],
            [],
        )
        i = SymbolRef("i", Long())
        c_ast = For(
            Assign(i, Constant(2)),
            Lt(i.copy(), Constant(10)),
            AddAssign(i.copy(), Constant(3)),
            [SymbolRef("foo")],
        )
        self._check(py_ast, c_ast)

    def test_for_0_args(self):
        py_ast = ast.For(ast.Name("i", ast.Load()),
            ast.Call(ast.Name("range", ast.Load()), [], [], None, None),
            [ast.Name("foo", ast.Load())],
            [],
        )
        with self.assertRaises(Exception):
          self._check(py_ast, None)

    def test_for_4_args(self):
        py_ast = ast.For(ast.Name("i", ast.Load()),
            ast.Call(ast.Name("range", ast.Load()),
                [Constant(1), Constant(2), Constant(3), Constant(4)], [], None, None),
            [ast.Name("foo", ast.Load())],
            [],
        )
        with self.assertRaises(Exception):
          self._check(py_ast, None)

    def test_for_expr_args(self):
        start = ast.BinOp(ast.Num(2), ast.Add(), ast.Num(3))
        stop = ast.BinOp(ast.Num(4), ast.Mult(), ast.Num(10))
        step = ast.BinOp(ast.Num(3), ast.Mod(), ast.Num(5))
        py_ast = ast.For(ast.Name("i", ast.Load()),
            ast.Call(ast.Name("range", ast.Load()), [start, stop, step], [], None, None),
            [ast.Name("foo", ast.Load())],
            [],
        )
        i = SymbolRef("i", Long())
        c_ast = For(
            Assign(i, Add(Constant(2), Constant(3))),
            Lt(i.copy(), Mul(Constant(4), Constant(10))),
            AddAssign(i.copy(), Mod(Constant(3), Constant(5))),
            [SymbolRef("foo")],
        )
        self._check(py_ast, c_ast)

    def test_AddAssign(self):
        py_ast = ast.AugAssign(ast.Name('i', ast.Load()), ast.Add(), ast.Num(3))
        c_ast = AddAssign(SymbolRef('i'), Constant(3))
        self._check(py_ast, c_ast)

    def test_SubAssign(self):
        py_ast = ast.AugAssign(ast.Name('i', ast.Load()),
                               ast.Sub(), ast.Num(3))
        c_ast = SubAssign(SymbolRef('i'), Constant(3))
        self._check(py_ast, c_ast)

    def test_MulAssign(self):
        py_ast = ast.AugAssign(ast.Name('i', ast.Load()),
                               ast.Mult(), ast.Num(3))
        c_ast = MulAssign(SymbolRef('i'), Constant(3))
        self._check(py_ast, c_ast)

    def test_DivAssign(self):
        py_ast = ast.AugAssign(ast.Name('i', ast.Load()),
                               ast.Div(), ast.Num(3))
        c_ast = DivAssign(SymbolRef('i'), Constant(3))
        self._check(py_ast, c_ast)
