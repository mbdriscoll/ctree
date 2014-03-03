import os
import copy
import shutil
import logging
import tempfile
import subprocess

import ctree
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
    self.c_program_text = ""
    log.info("Temporary compilation directory is: %s" % self.compilation_dir)

  def __del__(self):
    log.info("Removing temporary compilation directory %s." % self.compilation_dir)
    if self.destroy_compilation_dir_on_exit:
      shutil.rmtree(self.compilation_dir)

  def load(self, node):
    """Convert node to LLVM IR and store the result in this module."""
    # generate program text
    program_txt = str(node)
    self.c_program_text = program_txt
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
    CC = ctree.config['jit']['CC']
    CFLAGS = ctree.config['jit']['CFLAGS']
    compile_cmd = "%s -emit-llvm %s -o %s -c %s" % (CC, CFLAGS, ll_bc_file, c_src_file)
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
    self.exec_engine = EngineBuilder.new(self.ll_module).mcjit(True).opt(3).create()
    c_func_ptr = self.exec_engine.get_pointer_to_function(ll_function)

    # cast c_func_ptr to python callable using ctypes
    cfunctype = tree.get_type()
    return cfunctype(c_func_ptr)


class TypedSpecializedFunction(object):
  def __init__(self, c_ast, entry_point_name):
    self.module = JitModule().load(c_ast.get_root())
    entry_point = c_ast.find(FunctionDecl, name=entry_point_name)
    self.fn = self.module.get_callable(entry_point)

  def __call__(self, *args, **kwargs):
    assert not kwargs, "Passing kwargs to SpecializedFunction.__call__ isn't supported."
    return self.fn(*args, **kwargs)


class LazySpecializedFunction(object):
  def __init__(self, py_ast, entry_point_name):
    self.original_tree = py_ast
    self.entry_point_name = entry_point_name
    self.c_functions = {} # typesig -> callable map

  def _value_to_ctype(self, arg):
    """Return a hashable value specifying the type of 'arg'."""
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

  def transform(self, tree, args):
    """
    Convert the AST 'tree' into a C AST, optionally taking advantage of the
    actual runtime arguments.
    """
    pass

  def __call__(self, *args, **kwargs):
    assert not kwargs, "Passing kwargs to specialized functions isn't supported."
    typesig = tuple(map(self._value_to_ctype, args))
    log.info("detected specialized function call with argument type signature: %s -> ?" % (typesig,))

    if typesig not in self.c_functions:
      log.info("specialized function cache miss.")
      c_ast = self.transform( copy.deepcopy(self.original_tree), args )
      VerifyOnlyCAstNodes().visit(c_ast)
      self.c_functions[typesig] = TypedSpecializedFunction(c_ast, self.entry_point_name)
    else:
      log.info("specialized function cache hit!")
    return self.c_functions[typesig](*args, **kwargs)

  # =====================================================


