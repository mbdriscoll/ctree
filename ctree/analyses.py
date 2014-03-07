"""
validation of ast trees
"""
from ctree.visitors import NodeVisitor
from ctree.nodes import CtreeNode, ast
from ctree.c.nodes import SymbolRef


class DeclFinder(NodeVisitor):
    """
    Returns the first use of a particular symbol.
    """

    def __init__(self):
        self.decl = None

    def find(self, node):
        "look for a declaration of a symbol ref"
        assert isinstance(node, SymbolRef), \
            "DeclFinder only works on SymbolRefs for now."

        self.decl = None

        assert self.decl is not None, \
            "Couldn't find declaration for symbol %s." % node
        return self.decl


class AstValidationError(Exception):
    """
    Exception for non C nodes in an AST
    """
    pass


class VerifyOnlyCtreeNodes(NodeVisitor):
    """
    Checks that every node in the tree is an instance of
    ctree.nodes.common.CtreeNode. Raises an exception if a bad node
    is found.
    """

    def visit(self, node):
        if not isinstance(node, CtreeNode):
            raise AstValidationError("Expected a pure C ast, but found a non-CtreeNode: %s." % node)
        self.generic_visit(node)


class VerifyParentPointers(NodeVisitor):
    """
    Checks that parent pointers are set correctly, and throws
    an AstValidationError if they're not.
    """

    def _check(self, child, parent):
        "throw if child.parent is not the actual parent"
        if child.parent != parent:
            raise AstValidationError("Expect parent of %s to be %s, but got %s instead." %
                                     (child, parent, child.parent))

    def generic_visit(self, node):
        for _, child in ast.iter_fields(node):
            if type(child) is list:
                for grandchild in child:
                    self._check(grandchild, node)
                    self.visit(grandchild)
            elif isinstance(child, ast.AST):
                self._check(child, node)
                self.visit(child)
