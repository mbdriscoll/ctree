"""
Parses the python AST below, transforms it to C, JITs it, and runs it.
"""

import ast
import copy

from ctree.nodes import *
from ctree.dotgen import to_dot
from ctree.transformations import *
from ctree.analyses import VerifyOnlyCAstNodes
from ctree.jit import JitModule

import numpy as np

import logging
logging.basicConfig(level=20)
log = logging.getLogger(__name__)

def doubler(A):
  for i in range(len(A)):
    A[i] *= 2

def fib(n):
  if n < 2:
    return n
  else:
    return fib(n-1) + fib(n-2)

class JitFunction(object):
  pass


class SpecializedFunction(object):
  def __init__(self, c_ast):
    assert isinstance(c_ast, FunctionDecl)
    self.module = JitModule().load(c_ast.get_root())
    self.fn = self.module.get_callable(c_ast)

  def __call__(self, *args, **kwargs):
    assert not kwargs, "Passing kwargs to SpecializedFunction.__call__ isn't supported."
    return self.fn(*args, **kwargs)


class LazyTreeBuilder(object):
  def __init__(self, tree):
    self.original_tree = tree
    self.c_functions = {} # typesig -> callable map

  def _value_to_ctype_type(self, arg):
    if   type(arg) == int:   return ctypes.c_int
    elif type(arg) == float: return ctypes.c_float

    # check for numpy types
    try:
      import numpy
      if type(arg) == numpy.ndarray:
        return type(numpy.ctypeslib.as_ctypes(arg))
    except ImportError:
      pass

    raise Exception("Cannot determine ctype for Python object: %d (type %s)." % \
      (arg, type(arg)))

  @staticmethod
  def _transform(tree):
    transformations = [
      PyCtypesToCtreeTypes(),
      PyBasicConversions(),
      FixUpParentPointers(),
    ]
    for nth, tx in enumerate(transformations):
      tree = tx.visit(tree)
    VerifyOnlyCAstNodes().visit(tree)
    return tree

  def __call__(self, *args, **kwargs):
    assert not kwargs, "Passing kwargs to specialized functions isn't supported."
    typesig = tuple(map(self._value_to_ctype_type, args))
    log.info("detected specialized function call with argument type signature: %s -> ?" % typesig)

    if typesig not in self.c_functions:
      log.info("handling specialized function cache miss")
      # update tree with arg types
      py_ast = copy.deepcopy(self.original_tree)

      assert isinstance(py_ast, ast.FunctionDef)
      assert len(typesig) == len(py_ast.args.args)
      for arg, type in zip(py_ast.args.args, typesig):
        arg.annotation = type
        print("Set %s to type %s" % (arg, arg.annotation))
      py_ast.returns = PyCtypesToCtreeTypes._convert_to_ctree_type(typesig[0])

      c_ast = self._transform(py_ast)
      spec_func = SpecializedFunction(c_ast)

      self.c_functions[typesig] = spec_func
    else:
      log.info("specialized function cache hit!")

    return self.c_functions[typesig](*args, **kwargs)

  def get_callable(self, name):
    pass

  # =====================================================


def main():
  import ctree.frontend as frontend
  doubler_ast = frontend.get_ast(fib).body[0]

  c_doubler = LazyTreeBuilder(doubler_ast)
  print( c_doubler(11.0) )
  print( c_doubler(10) )
  print( c_doubler(11) )
  print( c_doubler(12) )
  print( c_doubler(13) )
  print( c_doubler(14) )
  print( c_doubler(15) )

  """
  actual   = np.ones(10, dtype=np.float32)
  expected = np.ones(10, dtype=np.float32)

  c_doubler(actual)
  doubler(expected)

  np.testing.assert_array_equal(actual, expected)
  """
  log.info("Success.")

if __name__ == '__main__':
  main()
