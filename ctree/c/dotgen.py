"""
DOT generator for C constructs.
"""

from ctree.dotgen import DotGenVisitor


class CDotGen(DotGenVisitor):
    """
    Manages generation of DOT.
    """

    def label_SymbolRef(self, node):
        if node.type:
            return r"%s %s" % (node.type, node.name)
        else:
            return r"%s" % (node.name)

    def label_FunctionDecl(self, node):
        s = r""
        if node.static:
            s += r"static "
        if node.inline:
            s += r"inline "
        if node.kernel:
            s += r"__kernel "
        s += r"%s %s(...)" % (node.return_type, node.name)
        return s

    def label_Constant(self, node):
        return str(node.value)

    def label_String(self, node):
        return r'\" \"'.join(node.values)

    def label_CFile(self, node):
        return node.get_filename()

    def label_NdPointer(self, node):
        s = "dtype: %s\n" % node.ptr.dtype
        s += "ndim, shape:    %s, %s\n" % (node.ptr.ndim, node.ptr.shape)
        s += "flags: %s" % node.ptr.flags
        return s

    def label_BinaryOp(self, node):
        return type(node.op).__name__
