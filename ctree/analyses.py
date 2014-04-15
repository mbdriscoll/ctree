"""
validation of ast trees
"""
from ctree.visitors import NodeVisitor
from ctree.nodes import CtreeNode, ast
from ctree.c.nodes import SymbolRef
from ctree.util import flatten


class DeclFinder(NodeVisitor):
    """
    Returns the first use of a particular symbol.
    """

    def __init__(self):
        self.decl = None

    def find(self, node):
        """look for a declaration of a symbol ref"""
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
