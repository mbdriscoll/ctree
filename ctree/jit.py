import os
import copy
import shutil
import logging
import tempfile

import ctree
import ctypes
from ctree.ast import *
from ctree.c.nodes import *
from ctree.frontend import get_ast
from ctree.analyses import VerifyOnlyCtreeNodes

import llvm.core as ll

log = logging.getLogger(__name__)

class JitModule(object):
  """
  Manages compilation of multiple ASTs.
  """
  def __init__(self):
    self.compilation_dir = tempfile.mkdtemp(prefix="ctree-", dir=tempfile.gettempdir())
    self.ll_module = ll.Module.new('ctree')
    self.ll_exec_engine = None
    log.info("Temporary compilation directory is: %s" % self.compilation_dir)

  def __del__(self):
    if not ctree.config["jit"]["PRESERVE_SRC_DIR"]:
      log.info("Removing temporary compilation directory %s." % self.compilation_dir)
      shutil.rmtree(self.compilation_dir)

  def _link_in(self, submodule):
    self.ll_module.link_in(submodule)

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
    assert isinstance(c_ast, (File, Project)), \
      "_ConcreteSpecializedFunction expected a File or Project where it got a %s." % type(c_ast)
    self.module = c_ast.get_root().codegen()
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
    ctree.stats.log("specialized function call")
    assert not kwargs, "Passing kwargs to specialized functions isn't supported."
    log.info("detected specialized function call with arg types: %s" % [type(a) for a in args])

    args_subconfig = self._args_to_subconfig_safely(args)
    tuner_subconfig = self._next_tuning_config()
    program_config = (args_subconfig, tuner_subconfig)

    log.info("specializer returned subconfig for arguments: %s" % (args_subconfig,))
    log.info("tuner returned subconfig: %s" % (tuner_subconfig,))

    if program_config in self.c_functions:
      ctree.stats.log("specialized function cache hit")
      log.info("specialized function cache hit!")
    else:
      log.info("specialized function cache miss.")
      c_ast = self.transform( copy.deepcopy(self.original_tree), program_config )
      VerifyOnlyCtreeNodes().visit(c_ast)
      self.c_functions[program_config] = _ConcreteSpecializedFunction(c_ast, self.entry_point_name)

    return self.c_functions[program_config](*args)

  def tune(*args, **kwargs):
    # TODO here's the tuning hook!
    for program_config in self._next_tuning_config():
      pass


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
