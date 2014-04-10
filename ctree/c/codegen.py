"""
Code generator for C constructs.
"""

from ctree.codegen import CodeGenVisitor
from ctree.c.nodes import Op
from ctree.c.types import Ptr, get_ctree_type
from ctree.precedence import UnaryOp, BinaryOp, TernaryOp, Cast
from ctree.precedence import get_precedence, is_left_associative


class CCodeGen(CodeGenVisitor):
    """
    Manages generation of C code.
    """

    def _requires_parentheses(self, node):
        """
        Return True if the current precedence is less than the
        parent precedence.  If the precedences are equal, check whether the
        node's orientation to the parent matches associativity.  If it doesn't,
        enclose with parentheses.
        """
        parent = getattr(node, 'parent', None)
        if isinstance(node, (UnaryOp, BinaryOp, TernaryOp)) and\
                isinstance(parent, (UnaryOp, BinaryOp, TernaryOp, Cast)):
            prec = get_precedence(node)
            parent_prec = get_precedence(parent)
            is_not_last_child = isinstance(parent, UnaryOp) or\
                                isinstance(parent, Cast) or\
                                (isinstance(parent, BinaryOp) and node is parent.left) or\
                                (isinstance(parent, TernaryOp) and node is not parent.elze)
            assoc_left = is_left_associative(parent)
            if (prec < parent_prec) or \
                    (prec == parent_prec and (assoc_left is not is_not_last_child)):
                return True
        return False

    # -------------------------------------------------------------------------
    # visitor methods

    def visit_FunctionDecl(self, node):
        params = ", ".join(map(str, node.params))
        s = ""
        if node.kernel:
            s += "__kernel "
        if node.static:
            s += "static "
        if node.inline:
            s += "inline "
        s += "%s %s(%s)" % (node.return_type, node.name, params)
        if node.defn:
            s += " %s" % self._genblock(node.defn)
        return s

    def visit_UnaryOp(self, node):
        if isinstance(node.op, (Op.PostInc, Op.PostDec)):
            s = "%s %s" % (node.arg, node.op)
        else:
            s = "%s %s" % (node.op, node.arg)
        return self._parentheses(node) % s

    def visit_BinaryOp(self, node):
        if isinstance(node.op, Op.ArrayRef):
            s = "%s[%s]" % (node.left, node.right)
        else:
            s = "%s %s %s" % (node.left, node.op, node.right)
        return self._parentheses(node) % s

    def visit_AugAssign(self, node):
        return "%s %s= %s" % (node.target, node.op, node.value)

    def visit_TernaryOp(self, node):
        s = "%s ? %s : %s" % (node.cond, node.then, node.elze)
        return self._parentheses(node) % s

    def visit_Cast(self, node):
        s = "(%s) %s" % (node.type, node.value)
        return self._parentheses(node) % s

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            return "'%s'" % node.value[0]
        else:
            return str(node.value)

    def visit_SymbolRef(self, node):
        s = ""
        if node._global:
            s += "__global "
        if node._local:
            s += "__local "
        if node._const:
            s += "const "
        if node.type:
            s += "%s " % node.type
        return "%s%s" % (s, node.name)

    def visit_Block(self, node):
        return self._genblock(node.body)

    def visit_Return(self, node):
        if node.value:
            return "return %s" % node.value
        else:
            return "return"

    def visit_If(self, node):
        then = self._genblock(node.then)
        if node.elze:
            elze = self._genblock(node.elze)
            return "if (%s) %s else %s" % (node.cond, then, elze)
        else:
            return "if (%s) %s" % (node.cond, then)

    def visit_While(self, node):
        body = self._genblock(node.body)
        return "while (%s) %s" % (node.cond, body)

    def visit_DoWhile(self, node):
        body = self._genblock(node.body)
        return "do %s while (%s)" % (body, node.cond)

    def visit_For(self, node):
        body = self._genblock(node.body)
        return "for (%s; %s; %s) %s" % (node.init, node.test, node.incr, body)

    def visit_FunctionCall(self, node):
        args = ", ".join(map(str, node.args))
        return "%s(%s)" % (node.func, args)

    def visit_String(self, node):
        return '"%s"' % '" "'.join(node.values)

    def visit_CFile(self, node):
        stmts = self._genblock(node.body, insert_curly_brackets=False, increase_indent=False)
        return '// <file: %s>%s' % (node.get_filename(), stmts)

    def visit_Void(self, node):
        return "void"

    def visit_Char(self, node):
        return "char"

    def visit_UChar(self, node):
        return "unsigned char"

    def visit_Short(self, node):
        return "short"

    def visit_UShort(self, node):
        return "unsigned short"

    def visit_Int(self, node):
        return "int"

    def visit_UInt(self, node):
        return "unsigned int"

    def visit_Long(self, node):
        return "long"

    def visit_ULong(self, node):
        return "unsigned long"

    def visit_Float(self, node):
        return "float"

    def visit_Double(self, node):
        return "double"

    def visit_LongDouble(self, node):
        return "long double"

    def visit_Ptr(self, node):
        base = node.base_type.codegen()
        return "%s*" % base

    def visit_NdPointer(self, node):
        inner_type = get_ctree_type(node.ptr._dtype_)
        return "%s" % Ptr(inner_type).codegen()

    def visit_FILE(self, node):
        return "FILE"
