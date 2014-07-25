import ast
import sys
import unittest

from ctypes import c_long

from fixtures.sample_asts import *
from ctree.transformations import *
from ctree.c.nodes import *
from ctree.frontend import get_ast


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
    def _check(self, py_ast, expected_c_ast, names_dict ={}, constants_dict={}):
        actual_c_ast = PyBasicConversions(names_dict, constants_dict).visit(py_ast)
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
        i = SymbolRef("i", c_long())
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
        i = SymbolRef("i", c_long())
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
        i = SymbolRef("i", c_long())
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
        i = SymbolRef("i", c_long())
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

    def test_Assign(self):
        py_ast = ast.Assign([ast.Name('i', ast.Load())],
                            ast.Num(3))
        c_ast = Assign(SymbolRef('i'), Constant(3))
        self._check(py_ast, c_ast)

    def test_namesDict(self):
        py_ast = ast.Name('i',ast.Load())
        c_ast = SymbolRef('d')
        self._check(py_ast,c_ast,names_dict={'i':'d'})

    def test_constantsDict(self):
        py_ast = ast.Name('i',ast.Load())
        c_ast = Constant(234)
        self._check(py_ast,c_ast,constants_dict={'i':234})

    def test_Subscript(self):
        py_ast = ast.Subscript(value=ast.Name('i',ast.Load()),
                               slice=ast.Index(value=ast.Num(n=1), ctx=ast.Load()))
        c_ast = ArrayRef(SymbolRef('i'),Constant(1))
        self._check(py_ast,c_ast)