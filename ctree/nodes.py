"""
Defines the hierarchy of AST nodes.
"""

import logging

log = logging.getLogger(__name__)

import ast

from ctree.codegen import CodeGenVisitor
from ctree.dotgen import DotGenVisitor
from ctree.util import flatten


class CtreeNode(ast.AST):
    """Base class for all AST nodes in ctree."""
    _fields = []

    def __init__(self):
        """Initialize a new AST Node."""
        super(CtreeNode, self).__init__()
        self.parent = None

    def __setattr__(self, name, value):
        """Set attribute and preserve parent pointers."""
        if name != "parent":
            for child in flatten(value):
                if isinstance(child, CtreeNode):
                    child.parent = self
        super(CtreeNode, self).__setattr__(name, value)

    def __str__(self):
        return self.codegen()

    def codegen(self, indent=0):
        raise Exception("Node class %s should override codegen()" % type(self))

    def _to_dot(self):
        """Retrieve the AST in DOT format for vizualization."""
        raise Exception("Node class %s should override _to_dot()" % type(self))

    def _requires_semicolon(self):
        """When coverted to a string, this node should be followed by a semicolon."""
        return True

    def get_root(self):
        """
        Traverse the parent pointer list to find the eldest
        parent without a parent, aka the root.
        """
        root = self
        while root.parent is not None:
            root = root.parent
        return root

    def find_all(self, node_class, **kwargs):
        """
        Returns a generator that yields all nodes of type
        'node_class' type whose attributes match those specified
        in kwargs. For example, all FunctionDecls with name 'fib'
        can be accessed via:
            my_ast.find_all(FunctionDecl, name="fib")
        """

        def pred(node):
            if type(node) == node_class:
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

    def replace(self, new_node):
        """
        Replace the current node with 'new_node'.
        """
        parent = self.parent
        assert self.parent, "Tried to replace a node without a parent."
        for fieldname, child in ast.iter_fields(parent):
            if child is self:
                setattr(parent, fieldname, new_node)
            elif isinstance(child, list) and self in child:
                child[child.index(self)] = new_node
        return new_node

    def insert_before(self, older_sibling):
        """
        Insert the given node just before 'self' in the current scope. Requires
        that 'self' be contained in a list.
        """
        parent = self.parent
        assert self.parent, "Tried to insert_before a node without a parent."
        for fieldname, child in ast.iter_fields(parent):
            if isinstance(child, list) and self in child:
                child.insert(child.index(self), older_sibling)
                return
        raise Exception("Couldn't perform insertion.")

    def insert_after(self, younger_sibling):
        """
        Insert the given node just before 'self' in the current scope. Requires
        that 'self' be contained in a list.
        """
        parent = self.parent
        assert self.parent, "Tried to insert_before a node without a parent."
        for fieldname, child in ast.iter_fields(parent):
            if isinstance(child, list) and self in child:
                child.insert(child.index(self) + 1, younger_sibling)
                return
        raise Exception("Couldn't perform insertion.")


# ---------------------------------------------------------------------------
# Common nodes

class CommonNode(CtreeNode):
    """Miscellaneous IR nodes."""

    def codegen(self, indent=0):
        return CommonCodeGen(indent).visit(self)

    def _to_dot(self):
        return CommonDotGen().visit(self)


class Project(CommonNode):
    """Holds a list files."""
    _fields = ['files']

    def __init__(self, files=None):
        self.files = files if files else []
        super(Project, self).__init__()

    def codegen(self, indent=0):
        """
        Code generates each file in the project and links their
        bytecode together to get the master bytecode file.
        """
        from ctree.jit import JitModule

        module = JitModule()

        # now that we have a concrete compilation dir, resolve references to it
        from ctree.transformations import ResolveGeneratedPathRefs

        resolver = ResolveGeneratedPathRefs(module.compilation_dir)
        self.files = [resolver.visit(f) for f in self.files]
        log.info("automatically resolved %d GeneratedPathRef node(s).", resolver.count)

        # transform all files into llvm modules and link them into the master module
        for f in self.files:
            submodule = f._compile(f.codegen(), module.compilation_dir)
            if submodule:
                module._link_in(submodule)
        return module


class File(CommonNode):
    """Holds a list of statements."""
    _fields = ['body']

    def __init__(self, name="generated", body=None):
        self.name = name
        self.body = body if body else []

    def codegen(self, *args):
        """Convert this substree into program text (a string)."""
        raise Exception("%s should override codegen()." % type(self))

    def _compile(self, program_text, compilation_dir):
        """Construct an LLVM module with the translated contents of this file."""
        raise Exception("%s should override _compile()." % type(self))

    def get_generated_path_ref(self):
        """Returns an object that can resolve the full file path at compile time."""
        return GeneratedPathRef(self)

    def get_filename(self):
        return "%s.%s" % (self.name, self._ext)


class GeneratedPathRef(CommonNode):
    """Represents a path to a generated file."""

    def __init__(self, target_file=None):
        assert isinstance(target_file, File), \
            "Cannot create a GeneratedPathRef to a %s, must be a File." % repr(target_file)
        self.target = target_file


class CommonCodeGen(CodeGenVisitor):
    """Manages conversion of all common nodes to txt."""

    def visit_File(self, node):
        return ";\n".join(map(str, node.body)) + ";\n"

    def visit_GeneratedPathRef(self, node):
        raise Exception("Unresolved GeneratedPathRefs to file %s." % (node.target.get_filename()))


class CommonDotGen(DotGenVisitor):
    """Manages coversion of all common nodes to dot."""

    def label_GeneratedPathRef(self, node):
        return "target: %s" % node.target.get_filename()
