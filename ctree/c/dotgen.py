"""
DOT generator for C constructs.
"""

from ctree.dotgen import DotGenLabeller
from ctree.types import codegen_type


class CDotGenLabeller(DotGenLabeller):
    """
    Manages generation of DOT.
    """

    def visit_SymbolRef(self, node):
        s = r""
        if node._global:
            s += r"__global "
        if node._local:
            s += r"__local "
        if node._const:
            s += r"__const "
        if node.type:
            s += r"%s " % codegen_type(node.type)
        s += r"%s" % node.name
        return s

    def visit_FunctionDecl(self, node):
        s = r""
        if node.static:
            s += r"static "
        if node.inline:
            s += r"inline "
        if node.kernel:
            s += r"__kernel "
        s += r"%s %s(...)" % (codegen_type(node.return_type), node.name)
        return s

    def visit_Constant(self, node):
        return str(node.value)

    def visit_String(self, node):
        return r'\" \"'.join(node.values)

    def visit_CFile(self, node):
        return node.get_filename()

    def visit_NdPointer(self, node):
        s = "dtype: %s\n" % node.ptr.dtype
        s += "ndim, shape:    %s, %s\n" % (node.ptr.ndim, node.ptr.shape)
        s += "flags: %s" % node.ptr.flags
        return s

    def visit_BinaryOp(self, node):
        return type(node.op).__name__

    def visit_UnaryOp(self, node):
        return type(node.op).__name__
