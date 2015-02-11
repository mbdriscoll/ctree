"""
Defines the hierarchy of AST nodes.
"""

import logging
import os.path

log = logging.getLogger(__name__)

import ast
import collections

from ctree.codegen import CodeGenVisitor
from ctree.dotgen import DotGenVisitor, DotGenLabeller
from ctree.util import flatten
import ctree
import os


class CtreeNode(ast.AST):
    """Base class for all AST nodes in ctree."""
    _fields = []

    def __init__(self):
        """Initialize a new AST Node."""
        super(CtreeNode, self).__init__()
        self.deleted = False
        self._force_parentheses = False

    def __str__(self):
        return self.codegen()

    def codegen(self, indent=0):
        raise Exception("Node class %s should override codegen()" % type(self))

    def delete(self):
        self.codegen = self.no_code_gen
        self.deleted = True

    def no_code_gen(self, *args):
        return ""

    def to_dot(self):
        """Retrieve the AST in DOT format for vizualization."""
        return "digraph mytree {\n%s}" % self._to_dot()

    def _to_dot(self):
        """Retrieve the AST in DOT format for vizualization."""
        return DotGenVisitor().visit(self)

    def _requires_semicolon(self):
        """When coverted to a string, this node should be followed by a semicolon."""
        return True

    def find_all(self, node_class, **kwargs):
        """
        Returns a generator that yields all nodes of type
        'node_class' type whose attributes match those specified
        in kwargs. For example, all FunctionDecls with name 'fib'
        can be accessed via:
            my_ast.find_all(FunctionDecl, name="fib")
        """

        def pred(node):
            if isinstance(node, node_class):
                for attr, value in kwargs.items():
                    try:
                        if getattr(node, attr) != value:
                            break
                    except AttributeError:
                        break
                else:
                    return True
            return False

        return self.find_if(pred)

    def find(self, node_class, **kwargs):
        """
        Returns one node of type 'node_class' whose attributes
        match those specified in kwargs, or None if no nodes
        can be found.
        """
        matching = self.find_all(node_class, **kwargs)
        try:
            return next(matching)
        except StopIteration:
            return None

    def find_if(self, pred):
        """
        Returns all nodes satisfying the given predicate,
        or None if no satisfactory nodes are found. The search
        starts from the current node.
        """
        for node in ast.walk(self):
            if pred(node):
                yield node

    def lift(self, **kwargs):
        for key, val in kwargs.items():
            attr = "_lift_%s" % key
            setattr(self, attr, getattr(self, attr, []) + val)
            type(self)._fields.append(attr)

    def __eq__(self, other):
        """Two nodes are equal if their attributes are equal."""
        return self.__dict__ == getattr(other, '__dict__', None)


# ---------------------------------------------------------------------------
# Common nodes

class CommonNode(CtreeNode):
    """Miscellaneous IR nodes."""

    def codegen(self, indent=0):
        return CommonCodeGen(indent).visit(self)

    def label(self):
        return CommonDotGen().visit(self)


class Project(CommonNode):
    """Holds a list files."""
    _fields = ['files']

    def __init__(self, files=None, indent=0, compilation_dir = ''):
        self.files = files if files else []
        super(Project, self).__init__()
        self.compilation_dir = compilation_dir
        self.indent = indent

    def codegen(self, indent=0):
        """
        Code generates each file in the project and links their
        bytecode together to get the master bytecode file.
        """
        from ctree.jit import JitModule

        self._module = JitModule()

        # now that we have a concrete compilation dir, resolve references to it
        from ctree.transformations import ResolveGeneratedPathRefs
        #
        # resolver = ResolveGeneratedPathRefs(self._module.compilation_dir)
        # self.files = [resolver.visit(f) for f in self.files]
        # if resolver.count:
        #     log.info("automatically resolved %d GeneratedPathRef node(s).", resolver.count)

        # transform all files into llvm modules and link them into the master module
        for f in self.files:
            submodule = f._compile(f.codegen())
            if submodule:
                self._module._link_in(submodule)
        return self._module

    @property
    def module(self):
        if self._module:
            return self._module
        return self.codegen(indent=self.indent)


class File(CommonNode):
    """Holds a list of statements."""
    _fields = ['body']
    _empty = None


    def __init__(self, name="generated", body=None, path = None):
        self.name = name
        self.body = body or []
        self.config_target = 'c'
        self.path = path or ctree.CONFIG.get('jit','COMPILE_PATH')
        self._program_hash = None

    @property
    def empty(self):
        if not self._empty:
            self._empty = type(self)(name=self.name, path=self.path).codegen()
        return self._empty


    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = value
        if not os.path.exists(self._path):
            os.makedirs(self._path)

    def get_hash_filename(self):
        return "%s.%s.sha" % (self.name, self._ext)


    @property
    def program_hash(self):
        if not os.path.exists(os.path.join(self.path, self.get_hash_filename())):
            return False
        if self._program_hash:
            return self._program_hash
        with open(os.path.join(self.path, self.get_hash_filename())) as h_file:
            return h_file.read().strip()

    @program_hash.setter
    def program_hash(self, value):
        self._program_hash = value
        with open(os.path.join(self.path, self.get_hash_filename()), 'w') as h_file:
            h_file.write(value)

    def codegen(self, *args):
        """Convert this substree into program text (a string)."""
        raise Exception("%s should override codegen()." % type(self))

    def _compile(self, program_text, compilation_sub_dir):
        """Construct an LLVM module with the translated contents of this file."""
        raise Exception("%s should override _compile()." % type(self))

    def get_generated_path_ref(self):
        """Returns an object that can resolve the full file path at compile time."""
        return GeneratedPathRef(self)

    def get_filename(self):
        return "%s.%s" % (self.name, self._ext)


class GeneratedPathRef(CommonNode):
    """Represents a path to a generated file."""
    _force_parentheses = False

    def __init__(self, target_file=None):
        assert isinstance(target_file, File), \
            "Cannot create a GeneratedPathRef to a %s, must be a File." % repr(target_file)
        self.target = target_file


class CommonCodeGen(CodeGenVisitor):
    """Manages conversion of all common nodes to txt."""

    def visit_File(self, node):
        return ";\n".join(map(str, node.body)) + ";\n"

    def visit_GeneratedPathRef(self, node):
        return '"%s"'% (os.path.join(node.target.path, node.target.get_filename()))
        # raise Exception("Unresolved GeneratedPathRefs to file %s." % (node.target.get_filename()))

    def visit_Pass(self, node):
        return ""


class CommonDotGen(DotGenLabeller):
    """Manages coversion of all common nodes to dot."""

    def visit_GeneratedPathRef(self, node):
        return "target: %s" % node.target.get_filename()
