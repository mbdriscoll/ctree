"""
Code generator for C constructs.
"""

from ctree.codegen import CodeGenVisitor
from ctree.c.nodes import Op
from ctree.types import codegen_type
from ctree.precedence import UnaryOp, BinaryOp, TernaryOp, Cast
from ctree.precedence import get_precedence, is_left_associative


class CCodeGen(CodeGenVisitor):
    """
    Manages generation of C code.
    """

    def _requires_parentheses(self, parent, node):
        """
        Returns node as a string, optionally with parentheses around it if
        needed to enforce precendence rules.
        """
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
        s += "%s %s(%s)" % (codegen_type(node.return_type), node.name, params)
        if node.defn:
            s += " %s" % self._genblock(node.defn)
        return s

    def visit_UnaryOp(self, node):
        op  = self._parenthesize(node, node.op)
        arg = self._parenthesize(node, node.arg)
        if isinstance(node.op, (Op.PostInc, Op.PostDec)):
            return "%s %s" % (arg, op)
        else:
            return "%s %s" % (op, arg)

    def visit_BinaryOp(self, node):
        left  = self._parenthesize(node, node.left)
        right = self._parenthesize(node, node.right)
        if isinstance(node.op, Op.ArrayRef):
            return "%s[%s]" % (left, right)
        else:
            return "%s %s %s" % (left, node.op, right)

    def visit_AugAssign(self, node):
        return "%s %s= %s" % (node.target, node.op, node.value)

    def visit_TernaryOp(self, node):
        cond = self._parenthesize(node, node.cond)
        then = self._parenthesize(node, node.then)
        elze = self._parenthesize(node, node.elze)
        return "%s ? %s : %s" % (cond, then, elze)

    def visit_Cast(self, node):
        value = self._parenthesize(node, node.value)
        return "(%s) %s" % (codegen_type(node.type), value)

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
        if node.type is not None:
            s += "%s " % codegen_type(node.type)
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

    def visit_ArrayDef(self, node):
        body = ", ".join(map(str, node.body))
        return "%s[%s] = { %s }" % (node.target, node.size, body)
