"""
Just-in-time compilation support.
"""

import abc
import copy
import shutil
import tempfile
import os
import hashlib
import string
import re

import ctree
from ctree.nodes import Project
from ctree.analyses import VerifyOnlyCtreeNodes
from ctree.util import highlight
from ctree.frontend import get_ast

import ast

import llvm.core as ll

import logging
import inspect
import hashlib
import json

from ctree.c.nodes import CFile, FunctionDecl, FunctionCall, MultiNode
from ctree.ocl.nodes import OclFile
from ctree.nodes import File

from collections import namedtuple

import itertools


log = logging.getLogger(__name__)


def getFile(filepath):
    """
    Takes a filepath and returns a specialized File instance (i.e. OclFile, CFile, etc)
    """
    ext_map = {'.'+t._ext:t for t in (
        CFile, OclFile
    )}
    path, filename = os.path.split(filepath)
    name, ext = os.path.splitext(filename)
    filetype = ext_map[ext]
    return filetype(name=name, path=path)


class JitModule(object):
    """
    Manages compilation of multiple ASTs.
    """

    def __init__(self):
        '''compilation_dir specifies the name of the subfolder under COMPILE_PATH'''
        # write files to $TEMPDIR/ctree/run-XXXX
        # compile_to = os.path.expanduser(ctree.CONFIG.get('jit','COMPILE_PATH'))
        #
        # # makes sure that directories exists, otherwise creates
        # if not compile_to:
        #     compile_to = os.path.join(tempfile.gettempdir(), "ctree")
        #
        # if compilation_dir:
        #     self.compilation_dir = os.path.join(compile_to, compilation_dir)
        # else:
        #     self.compilation_dir = tempfile.mkdtemp(prefix="run-", dir=compile_to)
        # if not os.path.exists(self.compilation_dir):
        #     os.makedirs(self.compilation_dir)
        #
        # log.info('compiling to %s'%self.compilation_dir)
        self.ll_module = ll.Module.new('ctree')
        self.exec_engine = None
        # log.info("temporary compilation directory is: %s",
        #          self.compilation_dir)

    # def __del__(self):
    #     if not ctree.CONFIG.get("jit", "PRESERVE_SRC_DIR"):
    #         log.info("removing temporary compilation directory %s.",
    #                  self.compilation_dir)
    #         shutil.rmtree(self.compilation_dir)

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

    ProgramConfig = namedtuple('ProgramConfig',['args_subconfig', 'tuner_subconfig'])

    def __init__(self, py_ast = None):
        if py_ast is not None:
            raise TypeError('This functionality has been removed and the signature will be modified in future versions')
        self.original_tree = py_ast or get_ast(self.apply)
        self.concrete_functions = {}  # config -> callable map
        self._tuner = self.get_tuning_driver()

    @property
    def info_filename(self):
        return 'info.json'

    def get_info(self, path):
        info_filepath = os.path.join(path, self.info_filename)
        if not os.path.exists(info_filepath):
            return {'hash':None, 'files':[]}
        with open(info_filepath) as info_file:
            return json.load(info_file)

    def set_info(self, path, dictionary):
        info_filepath = os.path.join(path, self.info_filename)
        with open(info_filepath,'w') as info_file:
            return json.dump(dictionary, info_file)


    @staticmethod
    def _hash(o):
        if isinstance(o, dict):
            return hash(frozenset(
                LazySpecializedFunction._hash(item) for item in o.items()
            ))
        else:
            return hash(str(o))

    def __hash__(self):
        mro = type(self).mro()
        result = hashlib.sha512('')
        for klass in mro:
            if issubclass(klass, LazySpecializedFunction):
                result.update(inspect.getsource(klass).encode())
            else:
                pass
        return int(result.hexdigest(), 16)


    def config_to_dirname(self, program_config):
        """Returns the subdirectory name under .compiled/funcname"""
        # fixes the directory names and squishes invalid chars
        forbidden_chars = r"""/\?%*:|"<>()' """
        replace_table = string.maketrans(forbidden_chars, '_'*len(forbidden_chars))
        config_path = re.sub("_+","_", str(program_config).translate(replace_table))
        path = os.path.join(ctree.CONFIG.get('jit','COMPILE_PATH'),self.__class__.__name__, config_path)
        return path


    def __call__(self, *args, **kwargs):
        """
            Determines the program_configuration to be run. If it has yet to be
            built, build it. Then, execute it. If the selected program_configuration 
            for this function has already been code generated for, this method draws
            from the cache.
        """
        ctree.STATS.log("specialized function call")
        assert not kwargs, \
            "Passing kwargs to specialized functions isn't supported."

        log.info("detected specialized function call with arg types: %s",
                 [type(a) for a in args])

        args_subconfig = self.args_to_subconfig(args)
        tuner_subconfig = next(self._tuner.configs)
        program_config = self.ProgramConfig(args_subconfig, tuner_subconfig)
        dir_name = self.config_to_dirname(program_config)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)


        log.info("tuner subconfig: %s", tuner_subconfig)
        log.info("arguments subconfig: %s", args_subconfig)

        config_hash = dir_name

        if config_hash in self.concrete_functions:              # checks to see if the necessary code is in the run-time cache
            ctree.STATS.log("specialized function cache hit")
            log.info("specialized function cache hit!")
            csf = self.concrete_functions[config_hash]

        else:
            ctree.STATS.log("specialized function cache miss")
            log.info("specialized function cache miss.")
            info = self.get_info(dir_name)
            if hash(self) != info['hash']:                      # checks to see if the necessary code is in the persistent cache
                
                # need to run transform() for code generation
                log.info('Hash miss. Running Transform')
                ctree.STATS.log("Filesystem cache miss")
                transform_result = self.transform(
                    copy.deepcopy(self.original_tree),          # TODO: is this deepcopy really necessary?
                    program_config
                )
                if not isinstance(transform_result, (tuple, list)):
                    transform_result = (transform_result,)
                for source_file in transform_result:
                    assert isinstance(source_file, File), "Transform must return an iterable of Files"
                    source_file.path = dir_name
                new_info = {'hash': hash(self), 'files':[os.path.join(f.path, f.get_filename()) for f in transform_result]}
                self.set_info(dir_name, new_info)

            else:                                             
                log.info('Hash hit. Skipping transform')
                ctree.STATS.log('Filesystem cache hit')
                files = [getFile(path) for path in info['files']]
                transform_result = files

            csf = self.finalize(transform_result, program_config)
            assert isinstance(csf, ConcreteSpecializedFunction), "Expected a ctree.jit.ConcreteSpecializedFunction, but got a %s." % type(csf)
            self.concrete_functions[config_hash] = csf
        return csf(*args, **kwargs)

    @classmethod
    def from_function(cls, func, classname = ''):
        class Replacer(ast.NodeTransformer):
            def visit_Module(self, node):
                return MultiNode(body = [self.visit(i) for i in node.body])

            def visit_FunctionDef(self, node):
                if node.name == func.__name__:
                    node.name = 'apply'
                node.body = [self.visit(item) for item in node.body]
                return node

            def visit_Name(self, node):
                if node.id == func.__name__:
                    node.id = 'apply'
                return node


        def transform(self, tree, program_config):
            """
                Calls transform after renaming the function name to 'apply' since specializers are written assuming "apply"
            """
            tree = Replacer().visit(tree)
            return super(newClass, self).transform(tree, program_config)

        def __hash__(self):
            func_hash = int(hashlib.sha512(inspect.getsource(func).encode()).hexdigest(), 16)
            old_hash = hash(cls())
            return func_hash ^ old_hash
        newClass = type(classname or func.__name__, (cls, ), {'apply': staticmethod(func), '__hash__':
                                                 __hash__,
                                                 'transform': transform
                                                })

        return newClass


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

    def finalize(self, transform_result, program_config):
        """
        This function will be passed the result of transform.  The specializer
        should return an ConcreteSpecializedFunction.
        """
        raise NotImplementedError("Finalize must be implemented")

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

    @staticmethod
    def apply(*args):
        raise NotImplementedError()
