import ast

from ctree.visitors import NodeVisitor
from ctree.util import enumerate_flatten


def to_dot_for_py_ast_nodes(self):
    from ctree.py.dotgen import PyDotGen

    return PyDotGen().visit(self)


"""
Bind to_dot_for_py_ast_nodes to all classes that derive from ast.AST. Ideally
we'd be able to bind one method to ast.AST, but it's a built-in type so we
can't.
"""
for entry in ast.__dict__.values():
    try:
        if issubclass(entry, ast.AST):
            entry.to_dot = to_dot_for_py_ast_nodes
    except TypeError:
        pass


class DotGenVisitor(NodeVisitor):
    """
    Generates a representation of the AST in the DOT graph language.
    See http://en.wikipedia.org/wiki/DOT_(graph_description_language)

    We can use pydot to do this, instead of using plain string concatenation.
    """

    @staticmethod
    def _qualified_name(obj):
        """
        return object name with leading module
        """
        return "%s.%s" % (obj.__module__, obj.__name__)

    def label(self, node):
        """
        A string to provide useful information for visualization, debugging, etc.
        This routine will attempt to call a label_XXX routine for class XXX, if
        such a routine exists (much like the visit_XXX routines).
        """
        out_string = r"%s\n" % type(node).__name__
        labeller = getattr(self, "label_" + type(node).__name__, None)
        if labeller:
            out_string += labeller(node)
        return out_string

    def generic_visit(self, node):
        # label this node
        out_string = 'n%s [label="%s"];\n' % (id(node), self.label(node))

        # edge to parent
        if hasattr(node, 'parent') and node.parent is not None:
            out_string += 'n%s -> n%s [label="parent",style=dotted];\n' % (id(node), id(node.parent))

        # edges to children
        for fieldname, fieldvalue in ast.iter_fields(node):
            for index, child in enumerate_flatten(fieldvalue):
                if isinstance(child, ast.AST):
                    suffix = "".join(["[%d]" % i for i in index])
                    out_string += 'n%d -> n%d [label="%s%s"];\n' % (id(node), id(child), fieldname, suffix)
                    out_string += child.to_dot()
        return out_string
