"""
DOT generation for OpenCL.
"""

from ctree.dotgen import DotGenLabeller


class OclDotLabeller(DotGenLabeller):
    """
    Visitor to generator DOT.
    """
    def visit_OclFile(self, node):
        return node.get_filename()
