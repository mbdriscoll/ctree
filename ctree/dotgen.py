import ast

from ctree.visitors import NodeVisitor


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
        for fieldname, child in ast.iter_fields(node):
            if type(child) is list:
                for i, grandchild in enumerate(child):
                    out_string += 'n%d -> n%d [label="%s[%d]"];\n' % \
                         (id(node), id(grandchild), fieldname, i)
                    out_string += _to_dot(grandchild)
            elif isinstance(child, ast.AST):
                out_string += 'n%d -> n%d [label="%s"];\n' % (id(node), id(child), fieldname)
                out_string += _to_dot(child)
        return out_string


def _to_dot(node):
    """
    Convert node to DOT, even if it's a Python AST node.
    """
    from ctree.nodes import CtreeNode
    from ctree.py.dotgen import PyDotGen

    assert isinstance(node, ast.AST), \
        "Cannot convert %s to DOT." % type(node)
    if isinstance(node, CtreeNode):
        return node._to_dot()
    else:
        return PyDotGen().visit(node)


def to_dot(node):
    """
    Returns a DOT representation of 'node' suitable for viewing with a DOT viewer like Graphviz.
    """
    assert isinstance(node, ast.AST), \
        "Cannot convert %s to DOT." % type(node)
    return "digraph myprogram {\n%s}" % _to_dot(node)
