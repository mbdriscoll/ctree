"""
Just-in-time compilation support.
"""

import abc
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
        import os

        # write files to $TEMPDIR/ctree/run-XXXX
        ctree_dir = os.path.join(tempfile.gettempdir(), "ctree")
        if not os.path.exists(ctree_dir):
            os.mkdir(ctree_dir)

        self.compilation_dir = tempfile.mkdtemp(prefix="run-", dir=ctree_dir)
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


class ConcreteSpecializedFunction(object):
    """
    A function backed by generated code.
    """
    __metaclass__ = abc.ABCMeta

    def _compile(self, entry_point_name, project_node, entry_point_typesig,
                 **kwargs):
        """
        Returns a python callable.
        """
        assert isinstance(project_node, Project), \
            "Expected a Project but it got a %s." % type(project_node)

        VerifyOnlyCtreeNodes().visit(project_node)

        self._module = project_node.codegen(**kwargs)

        highlighted = highlight(str(self._module.ll_module), 'llvm')
        log.debug("full LLVM program is: <<<\n%s\n>>>" % highlighted)

        return self._module.get_callable(entry_point_name, entry_point_typesig)

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class LazySpecializedFunction(object):
    """
    A callable object that will produce executable
    code just-in-time.
    """

    def __init__(self, py_ast):
        self.original_tree = py_ast
        self.concrete_functions = {}  # config -> callable map
        self._tuner = self.get_tuning_driver()

    @staticmethod
    def _hash(o):
        if isinstance(o, dict):
            return hash(frozenset(
                LazySpecializedFunction._hash(item) for item in o.items()
            ))
        else:
            return hash(str(o))

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

        config_hash = hash((self._hash(args_subconfig),
                            self._hash(tuner_subconfig)))

        if config_hash in self.concrete_functions:
            ctree.STATS.log("specialized function cache hit")
            log.info("specialized function cache hit!")
        else:
            ctree.STATS.log("specialized function cache miss")
            log.info("specialized function cache miss.")

            transform_result = self.transform(
                copy.deepcopy(self.original_tree),
                program_config
            )

            try:
                try:
                    csf = self.finalize(*transform_result)
                except TypeError:
                    csf = self.finalize(transform_result, program_config)
            except NotImplementedError:
                log.warn("""Your lazy specailized function has not implemented
                         finalize, assuming your output to transform is a
                         concrete specialized function.""")
                csf = transform_result

            assert isinstance(csf, ConcreteSpecializedFunction), \
                "Expected a ctree.jit.ConcreteSpecializedFunction, \
                 but got a %s." % type(csf)

            self.concrete_functions[config_hash] = csf

        return self.concrete_functions[config_hash](*args, **kwargs)

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

    def finalize(self, tree, program_config):
        """
        This function will be passed the result of transform.  The specializer
        should return an ConcreteSpecializedFunction.
        """
        raise NotImplementedError()

    def get_tuning_driver(self):
        """
        Define the space of possible implementations.
        """
        from ctree.tune import ConstantTuningDriver

        return ConstantTuningDriver()

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
