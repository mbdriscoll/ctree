import os
import copy
import shutil
import logging
import tempfile
import subprocess

from ctree.nodes.c import *
from ctree.frontend import get_ast
from ctree.analyses import VerifyOnlyCAstNodes

import llvm.core as ll

log = logging.getLogger(__name__)

class JitModule(object):
  """
  Manages compilation of multiple ASTs.
  """
  def __init__(self, destroy_compilation_dir_on_exit=True):
    self.compilation_dir = tempfile.mkdtemp(prefix="ctree-", dir=tempfile.gettempdir())
    self.ll_module = ll.Module('ctree_generated_code')
    self.ll_exec_engine = None
    self.destroy_compilation_dir_on_exit = destroy_compilation_dir_on_exit
    log.info("Temporary compilation directory is: %s" % self.compilation_dir)

  def __del__(self):
    log.info("Removing temporary compilation directory.")
    if self.destroy_compilation_dir_on_exit:
      shutil.rmtree(self.compilation_dir)

  def load(self, node):
    """Convert node to LLVM IR and store the result in this module."""
    # generate program text
    program_txt = str(node)
    log.info("Generated C Program: <<<\n%s\n>>>" % program_txt)

    # determine paths for C and LLVM bitcode files
    c_src_file = os.path.join(self.compilation_dir, "generated.c")
    ll_bc_file = os.path.join(self.compilation_dir, "generated.bc")
    log.info("File for generated C: %s" % c_src_file)
    log.info("File for generated LLVM: %s" % ll_bc_file)

    # write program text to C file
    with open(c_src_file, 'w') as c_file:
      c_file.write(program_txt)

    # call clang to generate LLVM bitcode file
    compile_cmd = "clang -emit-llvm -o %s -c %s" % (ll_bc_file, c_src_file)
    log.info("Compilation command: %s" % compile_cmd)
    subprocess.check_call(compile_cmd, shell=True)

    # load llvm bitcode
    with open(ll_bc_file, 'rb') as bc:
      self.ll_module = ll.Module.from_bitcode(bc)
    log.info("Generated LLVM Program: <<<\n%s\n>>>" % self.ll_module)

    # return self to aid in method chaining
    return self

  def get_callable(self, tree):
    """Returns a python callable that dispatches to the requested C function."""
    assert isinstance(tree, FunctionDecl)

    # get llvm represetation of function
    ll_function = self.ll_module.get_function_named(tree.name)

    # run jit compiler
    from llvm.ee import EngineBuilder
    self.exec_engine = EngineBuilder.new(self.ll_module).mcjit(True).create()
    c_func_ptr = self.exec_engine.get_pointer_to_function(ll_function)

    # cast c_func_ptr to python callable using ctypes
    cfunctype = tree.get_type().as_ctype()
    return cfunctype(c_func_ptr)


class TypedSpecializedFunction(object):
  def __init__(self, c_ast):
    assert isinstance(c_ast, FunctionDecl)
    self.module = JitModule().load(c_ast.get_root())
    self.fn = self.module.get_callable(c_ast)

  def __call__(self, *args, **kwargs):
    assert not kwargs, "Passing kwargs to SpecializedFunction.__call__ isn't supported."
    return self.fn(*args, **kwargs)


class LazySpecializedFunction(object):
  def __init__(self, py_ast):
    if isinstance(py_ast, ast.Module):
      py_ast = py_ast.body[0]
    assert isinstance(py_ast, ast.FunctionDef), \
      "Expected a FunctionDef to specialize."
    self.original_tree = py_ast
    self.c_functions = {} # typesig -> callable map

  def _value_to_ctype_type(self, arg):
    if   type(arg) == int:   return ctypes.c_int
    elif type(arg) == float: return ctypes.c_double

    # check for numpy types
    try:
      import numpy
      if type(arg) == numpy.ndarray:
        return type(numpy.ctypeslib.as_ctypes(arg))
    except ImportError:
      pass

    raise Exception("Cannot determine ctype for Python object: %d (type %s)." % \
      (arg, type(arg)))

  def transform(self, tree):
    pass

  def __call__(self, *args, **kwargs):
    assert not kwargs, "Passing kwargs to specialized functions isn't supported."
    typesig = tuple(map(self._value_to_ctype_type, args))
    log.info("detected specialized function call with argument type signature: %s -> ?" % typesig)

    if typesig not in self.c_functions:
      log.info("specialized function cache miss.")
      assert isinstance(self.original_tree, ast.FunctionDef)
      assert len(typesig) == len(self.original_tree.args.args)

      py_ast = copy.deepcopy(self.original_tree)
      for arg, type in zip(py_ast.args.args, typesig):
        arg.annotation = type

      c_ast = self.transform(py_ast)
      VerifyOnlyCAstNodes().visit(c_ast)
      self.c_functions[typesig] = TypedSpecializedFunction(c_ast)
    else:
      log.info("specialized function cache hit!")
    return self.c_functions[typesig](*args, **kwargs)

  def get_callable(self, name):
    pass

  # =====================================================


