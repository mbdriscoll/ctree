"""
DOT generation for OpenCL.
"""

from ctree.dotgen import DotGenVisitor


class OclDotGen(DotGenVisitor):
    """
    Visitor to generator DOT.
    """
    def label_OclFile(self, node):
        return node.get_filename()
