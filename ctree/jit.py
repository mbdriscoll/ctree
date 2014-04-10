"""just in time utilities"""
import copy
import shutil
import tempfile

import ctree
from ctree.nodes import Project
from ctree.analyses import VerifyOnlyCtreeNodes
from ctree.util import highlight

import llvm.core as ll

import logging

log = logging.getLogger(__name__)


class JitModule(object):
    """
    Manages compilation of multiple ASTs.
    """

    def __init__(self):
        self.compilation_dir = tempfile.mkdtemp(prefix="ctree-",
                                                dir=tempfile.gettempdir())
        self.ll_module = ll.Module.new('ctree')
        self.exec_engine = None
        log.info("temporary compilation directory is: %s",
                 self.compilation_dir)

    def __del__(self):
        if not ctree.CONFIG.get("jit", "PRESERVE_SRC_DIR"):
            log.info("removing temporary compilation directory %s.",
                     self.compilation_dir)
            shutil.rmtree(self.compilation_dir)

    def _link_in(self, submodule):
        self.ll_module.link_in(submodule)

    def get_callable(self, entry_point_name, entry_point_typesig):
        """
        Returns a python callable that dispatches to the requested C function.
        """

        # get llvm represetation of function
        ll_function = self.ll_module.get_function_named(entry_point_name)

        # run jit compiler
        from llvm.ee import EngineBuilder

        self.exec_engine = \
            EngineBuilder.new(self.ll_module).mcjit(True).opt(3).create()

        c_func_ptr = self.exec_engine.get_pointer_to_function(ll_function)

        # cast c_func_ptr to python callable using ctypes
        return entry_point_typesig(c_func_ptr)


class _ConcreteSpecializedFunction(object):
    """
    A function backed by generated code.
    """

    def __init__(self, entry_point_name, project, entry_point_typesig, extra_args=tuple()):
        assert isinstance(project, Project), \
            "Expected a Project but it got a %s." % type(project)
        assert project.parent is None, \
            "Expected null project.parent, but got: %s." % type(project.parent)

        VerifyOnlyCtreeNodes().visit(project)

        self.module = project.codegen()
        highlighted = highlight(str(self.module.ll_module), 'llvm')
        log.debug("full LLVM program is: <<<\n%s\n>>>" % highlighted)
        self.fn = self.module.get_callable(entry_point_name,
                                           entry_point_typesig)
        self._extra_args = extra_args

    def __call__(self, *args, **kwargs):
        assert not kwargs, \
            "Passing kwargs to SpecializedFunction.__call__ isn't supported."

        return self.fn(*(args + self._extra_args), **kwargs)


class LazySpecializedFunction(object):
    """
    A callable object that will produce executable
    code just-in-time.
    """

    def __init__(self, py_ast, entry_point_name):
        self.original_tree = py_ast
        self.entry_point_name = entry_point_name
        self.concrete_functions = {}  # config -> callable map
        self._tuner = self.get_tuning_driver()

    @staticmethod
    def _hash_dict(o):
        if isinstance(o, dict):
            return hash(frozenset(o.items()))
        else:
            return hash(o)

    def __call__(self, *args, **kwargs):
        """
        Determines the program_configuration to be run. If it has yet to be
        built, build it. Then, execute it.
        """
        ctree.STATS.log("specialized function call")
        assert not kwargs, \
            "Passing kwargs to specialized functions isn't supported."

        log.info("detected specialized function call with arg types: %s",
                 [type(a) for a in args])

        args_subconfig = self.args_to_subconfig(args)
        tuner_subconfig = next(self._tuner.configs)
        program_config = (args_subconfig, tuner_subconfig)

        log.info("tuner subconfig: %s", tuner_subconfig)
        log.info("arguments subconfig: %s", args_subconfig)

        config_hash = hash((self._hash_dict(args_subconfig),
                            self._hash_dict(tuner_subconfig)))

        if config_hash in self.concrete_functions:
            ctree.STATS.log("specialized function cache hit")
            log.info("specialized function cache hit!")
        else:
            ctree.STATS.log("specialized function cache miss")
            log.info("specialized function cache miss.")
            translator_result = self.transform(
                copy.deepcopy(self.original_tree),
                program_config
            )

            self.concrete_functions[config_hash] = _ConcreteSpecializedFunction(
                self.entry_point_name,
                *translator_result
            )

        return self.concrete_functions[config_hash](*args)

    def report(self, *args, **kwargs):
        """
        Records the performance of the most recent configuration.
        """
        return self._tuner.report(*args, **kwargs)

    # =====================================================
    # Methods to be overridden by the user

    def transform(self, tree, program_config):
        """
        Convert the AST 'tree' into a C AST, optionally taking advantage of the
        actual runtime arguments.
        """
        raise NotImplementedError()

    def get_tuning_driver(self):
        """
        Define the space of possible implementations.
        """
        from ctree.tune import NullTuningDriver

        return NullTuningDriver()

    def args_to_subconfig(self, args):
        """
        Extract features from the arguments to define uniqueness of
        this particular invocation. The return value must be a hashable
        object, or a dictionary of hashable objects.
        """
        log.warn("arguments will not influence program_config. " +
                 "Consider overriding args_to_subconfig() in %s.",
                 type(self).__name__)
        return dict()
