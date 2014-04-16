import ast

from ctree.visitors import NodeVisitor
from ctree.util import enumerate_flatten


def to_dot_inner_for_py_ast_nodes(self):
    from ctree.py.dotgen import PyDotGen

    return PyDotGen().visit(self)

def to_dot_outer_for_py_ast_nodes(self):
    return "digraph mytree {\n%s}" % self._to_dot()

"""
Bind to_dot_for_py_ast_nodes to all classes that derive from ast.AST. Ideally
we'd be able to bind one method to ast.AST, but it's a built-in type so we
can't.
"""
for entry in ast.__dict__.values():
    try:
        if issubclass(entry, ast.AST):
            entry._to_dot = to_dot_inner_for_py_ast_nodes
            entry.to_dot  = to_dot_outer_for_py_ast_nodes
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
        This routine will return the first successful call among:
        1) node.label()
        2) dotgenvisitor.label_XXX(node)
        """
        out_string = r"%s\n" % type(node).__name__
        if hasattr(node, 'label'):
            out_string += node.label()
        else:
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
                    out_string += child._to_dot()
        return out_string
