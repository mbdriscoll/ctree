import ast
import unittest

from fixtures import *
from ctree.transformations import *
from ctree.nodes import c
from ctree.frontend import get_ast

class TestSetParam(unittest.TestCase):

  def _check(self, func_type, tree):
    if isinstance(tree, c.FunctionDecl):
      self.assertEqual(tree.return_type, ct.c_long)
      for param, expected_type in zip(tree.params, func_type[1:]):
        self.assertEqual(param.type, expected_type)
    elif isinstance(tree, ast.FunctionDef):
      self.assertEqual(tree.returns, ct.c_long)
      for param, expected_type in zip(tree.args.args, func_type[1:]):
        self.assertEqual(param.annotation, expected_type)
    elif isinstance(tree, ast.Module):
      self._check(func_type, tree.body[0])
    else:
      self.fail("Can't check param setting on %s object." % tree)

  def test_no_args(self):
    func_type = [ct.c_long]
    func_decl = SetParamTypes("get_two", func_type).visit(get_two_ast)
    self._check(func_type, func_decl)

  def test_one_arg(self):
    func_type = [ct.c_long, ct.c_long]
    func_decl = SetParamTypes("fib", func_type).visit(fib_ast)
    self._check(func_type, func_decl)

  def test_two_args(self):
    func_type = [ct.c_long, ct.c_long, ct.c_long]
    func_decl = SetParamTypes("gcd", func_type).visit(gcd_ast)
    self._check(func_type, func_decl)

  def test_mixed_args(self):
    func_type = [ct.c_long, ct.c_double, ct.c_long, ct.c_long]
    func_decl = SetParamTypes("choose", func_type).visit(choose_ast)
    self._check(func_type, func_decl)

  def test_no_args(self):
    func_type = [ct.c_long]
    func_decl = SetParamTypes("get_two", func_type).visit( get_ast(get_two) )
    self._check(func_type, func_decl)

  def test_one_arg(self):
    func_type = [ct.c_long, ct.c_long]
    func_decl = SetParamTypes("fib", func_type).visit( get_ast(fib) )
    self._check(func_type, func_decl)

  def test_two_args(self):
    func_type = [ct.c_long, ct.c_long, ct.c_long]
    func_decl = SetParamTypes("gcd", func_type).visit( get_ast(gcd) )
    self._check(func_type, func_decl)

  def test_mixed_args(self):
    func_type = [ct.c_long, ct.c_double, ct.c_long, ct.c_long]
    func_decl = SetParamTypes("choose", func_type).visit( get_ast(choose) )
    self._check(func_type, func_decl)


class TestFixUpParentPointers(unittest.TestCase):
  def _check(self, root):
    from ctree.analyses import VerifyParentPointers
    VerifyParentPointers().visit(root)

  def test_identity(self):
    identity_ast.find(SymbolRef, name="x").parent = None
    tree = FixUpParentPointers().visit(identity_ast)
    self._check(tree)

  def test_fib(self):
    fib_ast.find(Constant, value=2).parent = None
    tree = FixUpParentPointers().visit(fib_ast)
    self._check(tree)

  def test_gcd(self):
    gcd_ast.find(Return).parent = None
    tree = FixUpParentPointers().visit(gcd_ast)
    self._check(tree)


class TestCtxScrubber(unittest.TestCase):

  def _check(self, tree):
    for node in ast.walk(tree):
      if isinstance(node, ast.Name):
        self.assertIsNone(node.ctx)

  def test_identity(self):
    tree = PyCtxScrubber().visit( get_ast(identity) )
    self._check(tree)

  def test_fib(self):
    tree = PyCtxScrubber().visit( get_ast(fib) )
    self._check(tree)

  def test_gcd(self):
    tree = PyCtxScrubber().visit( get_ast(gcd) )
    self._check(tree)


class TestStripDocstrings(unittest.TestCase):

  def foo():
    """my docstring"""
    pass
  class Bar():
    """my other docstring"""
    pass

  def _check(self, tree):
    for node in ast.walk(tree):
      if isinstance(node, ast.Str):
        print(node.s)
      self.assertNotIsInstance(node, ast.Str)

  def test_func_docstring(self):
    tree = StripPythonDocstrings().visit( get_ast(self.foo) )
    self._check(tree)

  def test_class_docstring(self):
    tree = StripPythonDocstrings().visit( get_ast(self.Bar) )
    self._check(tree)

  def test_subtree_docstrings(self):
    tree = StripPythonDocstrings().visit( ast.Module([
      get_ast(self.foo),
      get_ast(self.Bar),
    ]) )
    self._check(tree)
