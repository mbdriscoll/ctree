import os
import shutil
import tempfile
import subprocess

from ctree.nodes import *

import llvm.core as ll

class Module(object):
  """
  Manages compilation of multiple ASTs.
  """
  def __init__(self, destroy_compilation_dir_on_exit=True):
    self.compilation_dir = tempfile.mkdtemp(prefix="ctree-", dir=tempfile.gettempdir())
    self.ll_module = ll.Module('ctree_generated_code')
    self.ll_exec_engine = None
    self.destroy_compilation_dir_on_exit = destroy_compilation_dir_on_exit

  def __del__(self):
    if self.destroy_compilation_dir_on_exit:
      shutil.rmtree(self.compilation_dir)

  def compile(self, node):
    """Convert node to LLVM IR and store the result in this module."""
    # generate program text
    program_txt = str(node)
    print ("C Program:\n%s" % program_txt)

    # determine paths for C and LLVM bitcode files
    c_src_file = os.path.join(self.compilation_dir, "generated.c")
    ll_bc_file = os.path.join(self.compilation_dir, "generated.bc")

    # write program text to C file
    with open(c_src_file, 'w') as c_file:
      c_file.write(program_txt)

    # call clang to generate LLVM bitcode file
    compile_cmd = "clang -emit-llvm -o %s -c %s" % (ll_bc_file, c_src_file)
    subprocess.check_call(compile_cmd, shell=True)

    # load llvm bitcode
    with open(ll_bc_file, 'rb') as bc:
      self.ll_module = ll.Module.from_bitcode(bc)

    print ("LLVM Module:\n%s" % self.ll_module)

  def get_callable(self, tree):
    """Returns a python callable that dispatches to the requested C function."""
    assert isinstance(tree, FunctionDecl)

    # get llvm represetation of function
    name = tree.name.name
    ll_function = self.ll_module.get_function_named(name)

    # run jit compiler
    from llvm.ee import EngineBuilder
    self.exec_engine = EngineBuilder.new(self.ll_module).mcjit(True).create()
    c_func_ptr = self.exec_engine.get_pointer_to_function(ll_function)

    # cast c_func_ptr to python callable using ctypes
    cfunctype = tree.get_type().as_ctype()
    return cfunctype(c_func_ptr)
