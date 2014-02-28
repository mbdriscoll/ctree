import os
import copy
import shutil
import logging
import tempfile
import subprocess

import ctree
import ctypes
from ctree.nodes.c import *
from ctree.frontend import get_ast
from ctree.analyses import VerifyOnlyCtreeNodes

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
    log.info("Removing temporary compilation directory %s." % self.compilation_dir)
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


class _ConcreteSpecializedFunction(object):
  """
  A function backed by generated code.
  """
  def __init__(self, c_ast, entry_point_name):
    self.module = JitModule().load(c_ast.get_root())
    entry_point = c_ast.find(FunctionDecl, name=entry_point_name)
    self.fn = self.module.get_callable(entry_point)

  def __call__(self, *args, **kwargs):
    assert not kwargs, "Passing kwargs to SpecializedFunction.__call__ isn't supported."
    return self.fn(*args, **kwargs)


class LazySpecializedFunction(object):
  """
  A callable object that will produce executable
  code just-in-time.
  """
  def __init__(self, py_ast, entry_point_name):
    self.original_tree = py_ast
    self.entry_point_name = entry_point_name
    self.c_functions = {} # typesig -> callable map

  def _args_to_subconfig_safely(self, args):
    """
    Ask the instance for the component of the program configuration
    that comes from the arguments, and then verify that it's hashable.
    """
    subconfig = self.args_to_subconfig(args)
    try:
      hash(subconfig)
    except TypeError:
      raise Exception("args_to_subconfig must return a hashable type")
    return subconfig

  def _next_tuning_config(self):
    return ()

  def __call__(self, *args, **kwargs):
    """
    Determines the program_configuration to be run. If it has yet to be built,
    build it. Then, execute it.
    """
    assert not kwargs, "Passing kwargs to specialized functions isn't supported."
    log.info("detected specialized function call with arg types: %s" % [type(a) for a in args])

    args_subconfig = self._args_to_subconfig_safely(args)
    tuner_subconfig = self._next_tuning_config()
    program_config = (args_subconfig, tuner_subconfig)

    log.info("arguments yield subconfig: %s" % (args_subconfig,))
    log.info("tuner yields subconfig: %s" % (tuner_subconfig,))

    if program_config in self.c_functions:
      log.info("specialized function cache hit!")
    else:
      log.info("specialized function cache miss.")
      c_ast = self.transform( copy.deepcopy(self.original_tree), program_config )
      VerifyOnlyCtreeNodes().visit(c_ast)
      self.c_functions[program_config] = _ConcreteSpecializedFunction(c_ast, self.entry_point_name)

    return self.c_functions[program_config](*args)


  # =====================================================
  # Methods to be overridden by the user

  def transform(self, tree, program_config):
    """
    Convert the AST 'tree' into a C AST, optionally taking advantage of the
    actual runtime arguments.
    """
    return tree

  def set_tuning_space(self, space):
    """
    Define the space of possible implementations.
    """
    raise NotImplementedError()

  def args_to_subconfig(self, args):
    """
    Extract features from the arguments to define uniqueness of
    this particular invocation.
    """
    log.warn("arguments will not influence program_config. " + \
      "Consider overriding args_to_subconfig() in %s." % type(self).__name__)
    return ()
