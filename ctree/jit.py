"""
Just-in-time compilation support.
"""

import abc
import copy
import os
import shutil
import re
import atexit
import ast
import logging
import inspect
import hashlib
import json
from collections import namedtuple
import tempfile


import ctree
from ctree.nodes import Project
from ctree.analyses import VerifyOnlyCtreeNodes
from ctree.util import highlight
from ctree.frontend import get_ast, dump
from ctree.transformations import DeclarationFiller
from ctree.c.nodes import CFile, MultiNode
from ctree.ocl.nodes import OclFile
from ctree.nodes import File

# import llvmlite.binding as llvm
# llvm.initialize()
# llvm.initialize_native_target()

import logging

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
        import os

        # write files to $TEMPDIR/ctree/run-XXXX
        ctree_dir = os.path.join(tempfile.gettempdir(), "ctree")
        if not os.path.exists(ctree_dir):
            os.mkdir(ctree_dir)

        self.compilation_dir = tempfile.mkdtemp(prefix="run-", dir=ctree_dir)
        self.ll_module = None
        self.exec_engine = None

    def _link_in(self, submodule):
        self.so_file_name = submodule
        # if self.ll_module is not None:
        #     self.ll_module.link_in(submodule)
        # else:
        #     self.ll_module = submodule

    def get_callable(self, entry_point_name, entry_point_typesig):
        """
        Returns a python callable that dispatches to the requested C function.
        """

        # get llvm represetation of function
        # ll_function = self.ll_module.get_function(entry_point_name)
        import ctypes
        lib = ctypes.cdll.LoadLibrary(self.so_file_name)
        func_ptr = getattr(lib, entry_point_name)
        print(entry_point_typesig._argtypes_)
        func_ptr.argtypes = entry_point_typesig._argtypes_
        func_ptr.restype = entry_point_typesig._restype_
        # func = func_ptr

        # run jit compiler
        # from llvm.ee import EngineBuilder
        # self.exec_engine = llvm.create_jit_compiler(self.ll_module)

        # c_func_ptr = self.exec_engine.get_pointer_to_global(ll_function)

        # cast c_func_ptr to python callable using ctypes
        return func_ptr


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
    _directory_fields = ['__class__.__name__', 'backend_name']

    class NameExtractor(ast.NodeVisitor):
        """
        Extracts the first functiondef name found
        """
        def visit_FunctionDef(self, node):
            return node.name

        def generic_visit(self, node):
            for field, value in ast.iter_fields(node):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, ast.AST):
                            res = self.visit(item)
                            if res:
                                return res
                elif isinstance(value, ast.AST):
                    res = self.visit(value)
                    if res:
                        return res

    def __init__(self, py_ast=None, sub_dir=None, backend_name="default"):
        if py_ast is not None and self.apply is not LazySpecializedFunction.apply:
            raise TypeError('Cannot define apply and pass py_ast')
        self.original_tree = py_ast or (get_ast(self.apply) if self.apply is not LazySpecializedFunction.apply else None)
        self.concrete_functions = {}  # config -> callable map
        self._tuner = self.get_tuning_driver()
        self.sub_dir = sub_dir or self.NameExtractor().visit(self.original_tree) or hex(hash(self))[2:]
        self.backend_name = backend_name



    @property
    def original_tree(self):
        return copy.deepcopy(self._original_tree)

    @original_tree.setter
    def original_tree(self, value):
        if not hasattr(self, '_original_tree'):
            self._original_tree = value
        elif ast.dump(self.__original_tree, True, True) != ast.dump(value, True, True):
            raise AttributeError('Cannot redefine the ast')

    @property
    def info_filename(self):
        return 'info.json'

    def get_info(self, path):
        info_filepath = os.path.join(path, self.info_filename)
        if not os.path.exists(info_filepath):
            return {'hash': None, 'files':[]}
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
        result = hashlib.sha512(''.encode())
        for klass in mro:
            if issubclass(klass, LazySpecializedFunction):
                try:
                    result.update(inspect.getsource(klass).encode())
                except IOError:  # means source can't be found. Well, can't do anything about that I don't think
                    pass
            else:
                pass
        if self.original_tree is not None:
            tree_str = ast.dump(self.original_tree, annotate_fields=True, include_attributes=True)
            result.update(tree_str.encode())
        return int(result.hexdigest(), 16)


    def config_to_dirname(self, program_config):
        """Returns the subdirectory name under .compiled/funcname"""
        # fixes the directory names and squishes invalid chars
        regex_filter = re.compile(r"""[/\?%*:|"<>()'{} ]""")

        def deep_getattr(obj, s):
            parts = s.split('.')
            for part in parts:
                obj = getattr(obj, part)
            return obj

        path_parts = [
            self.sub_dir,
            str(self._hash(program_config.args_subconfig)),
            str(self._hash(program_config.tuner_subconfig))
            ]

        for attrib in self._directory_fields:
            path_parts.append(str(deep_getattr(self, attrib)))
        filtered_parts = [str(re.sub(regex_filter, '_', part)) for part in path_parts]
        compile_path = str(ctree.CONFIG.get('jit', 'COMPILE_PATH'))

        path = os.path.join(compile_path, *filtered_parts)


        return re.sub('_+','_', path)


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

        if ctree.CONFIG.getboolean('jit', 'CACHE') and config_hash in self.concrete_functions:              # checks to see if the necessary code is in the run-time cache
            ctree.STATS.log("specialized function cache hit")
            log.info("specialized function cache hit!")
            csf = self.concrete_functions[config_hash]

        else:
            ctree.STATS.log("specialized function cache miss")
            log.info("specialized function cache miss.")
            info = self.get_info(dir_name)

            if hash(self) != info['hash'] and self.original_tree is not None:                      # checks to see if the necessary code is in the persistent cache
                # need to run transform() for code generation
                log.info('Hash miss. Running Transform')
                ctree.STATS.log("Filesystem cache miss")
                transform_result = self.run_transform(program_config)

                # Saving files to cache directory
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


    def run_transform(self, program_config):
        transform_result = self.transform(
            self.original_tree,
            program_config
        )
        if not isinstance(transform_result, (tuple, list)):
            transform_result = (transform_result,)

        transform_result = [DeclarationFiller().visit(source_file)
                            if isinstance(source_file, CFile) else source_file
                            for source_file in transform_result]
        return transform_result



    @classmethod
    def from_function(cls, func, folder_name=''):
        class Replacer(ast.NodeTransformer):
            def visit_Module(self, node):
                return MultiNode(body=[self.visit(i) for i in node.body])

            def visit_FunctionDef(self, node):
                if node.name == func.__name__:
                    node.name = 'apply'
                node.body = [self.visit(item) for item in node.body]
                return node

            def visit_Name(self, node):
                if node.id == func.__name__:
                    node.id = 'apply'
                return node

        func_ast = Replacer().visit(get_ast(func))
        return cls(py_ast=func_ast, sub_dir=folder_name or func.__name__)



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
