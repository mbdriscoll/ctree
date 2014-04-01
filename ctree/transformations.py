"""
A set of basic transformers for python asts
"""
import os
import ast

from ctree.nodes import Project
from ctree.c.nodes import Op, Constant, String, SymbolRef, BinaryOp, TernaryOp, Return
from ctree.c.nodes import If, CFile, FunctionCall, FunctionDecl, For, Assign, AugAssign
from ctree.c.nodes import Lt, PostInc, AddAssign, SubAssign, MulAssign, DivAssign
from ctree.c.types import Long
from ctree.visitors import NodeTransformer


class PyCtxScrubber(NodeTransformer):
    """
    Removes pesky ctx attributes from Python ast.Name nodes,
    yielding much cleaner python asts.
    """

    def visit_Name(self, node):
        node.ctx = None
        return node


class PyBasicConversions(NodeTransformer):
    """
    Convert constructs with obvious C analogues.
    """
    PY_OP_TO_CTREE_OP = {
        ast.Add: Op.Add,
        ast.Mod: Op.Mod,
        ast.Mult: Op.Mul,
        ast.Sub: Op.Sub,
        ast.Lt: Op.Lt,
        # TODO list the rest
    }

    def visit_Num(self, node):
        return Constant(node.n)

    def visit_Str(self, node):
        return String(node.s)

    def visit_Name(self, node):
        return SymbolRef(node.id)

    def visit_BinOp(self, node):
        lhs = self.visit(node.left)
        rhs = self.visit(node.right)
        op = self.PY_OP_TO_CTREE_OP[type(node.op)]()
        return BinaryOp(lhs, op, rhs)

    def visit_Return(self, node):
        if hasattr(node, 'value'):
            return Return(self.visit(node.value))
        else:
            return Return()

    def visit_For(self, node):
        """restricted, for now, to range as iterator with long-type args"""
        if isinstance(node, ast.For) and \
           isinstance(node.iter, ast.Call) and \
           isinstance(node.iter.func, ast.Name) and \
           node.iter.func.id == 'range':
            Range = node.iter
            nArgs = len(Range.args)
            if nArgs == 1:
                stop = self.visit(Range.args[0])
                start, step = Constant(0), Constant(1)
            elif nArgs == 2:
                start, stop = map(self.visit, Range.args)
                step = Constant(1)
            elif nArgs == 3:
                start, stop, step = map(self.visit, Range.args)
            else:
                raise Exception("Cannot convert a for...range with %d args." % nArgs)

            # TODO allow any expressions castable to Long type
            assert stop.get_type()  == Long(), "Can only convert range's with stop values of Long type."
            assert start.get_type() == Long(), "Can only convert range's with start values of Long type."
            assert step.get_type()  == Long(), "Can only convert range's with step values of Long type."

            target = SymbolRef(node.target.id, Long())
            for_loop = For(
                Assign(target, start),
                Lt(target.copy(), stop),
                AddAssign(target.copy(), step),
                [self.visit(stmt) for stmt in node.body],
            )
            return for_loop
        node.body = list(map(self.visit, node.body))
        return node

    def visit_If(self, node):
        if isinstance(node, ast.If):
            cond = self.visit(node.test)
            then = [self.visit(t) for t in node.body]
            elze = [self.visit(t) for t in node.orelse] or None
            return If(cond, then, elze)
        else:
            return self.generic_visit(node)

    def visit_IfExp(self, node):
        cond = self.visit(node.test)
        then = self.visit(node.body)
        elze = self.visit(node.orelse)
        return TernaryOp(cond, then, elze)

    def visit_Compare(self, node):
        assert len(node.ops) == 1, \
            "PyBasicConversions doesn't support Compare nodes with more than one operator."
        lhs = self.visit(node.left)
        op = self.PY_OP_TO_CTREE_OP[type(node.ops[0])]()
        rhs = self.visit(node.comparators[0])
        return BinaryOp(lhs, op, rhs)

    def visit_Module(self, node):
        body = [self.visit(s) for s in node.body]
        return Project([CFile("module", body)])

    def visit_Call(self, node):
        args = [self.visit(a) for a in node.args]
        fn = self.visit(node.func)
        return FunctionCall(fn, args)

    def visit_FunctionDef(self, node):
        if ast.get_docstring(node):
            node.body.pop(0)
        params = [self.visit(p) for p in node.args.args]
        defn = [self.visit(s) for s in node.body]
        return FunctionDecl(None, node.name, params, defn)

    def visit_arg(self, node):
        return SymbolRef(node.arg, node.annotation)

    def visit_AugAssign(self, node):
        op = type(node.op)
        target = self.visit(node.target)
        value = self.visit(node.value)
        if op is ast.Add:
            return AddAssign(target, value)
        elif op is ast.Sub:
            return SubAssign(target, value)
        elif op is ast.Mult:
            return MulAssign(target, value)
        elif op is ast.Div:
            return DivAssign(target, value)
        # Error?
        return node


class FixUpParentPointers(NodeTransformer):
    """
    Add parent pointers if they're missing.
    """

    def generic_visit(self, node):
        for fieldname, child in ast.iter_fields(node):
            if type(child) is list:
                for grandchild in child:
                    setattr(grandchild, 'parent', node)
                    self.visit(grandchild)
            elif isinstance(child, ast.AST):
                setattr(child, 'parent', node)
                self.visit(child)
        return node


class ResolveGeneratedPathRefs(NodeTransformer):
    """
    Converts any instances of ctree.nodes.GeneratedPathRef into strings containing the absolute path
    of the target file.
    """

    def __init__(self, compilation_dir):
        self.compilation_dir = compilation_dir
        self.count = 0

    def visit_GeneratedPathRef(self, node):
        self.count += 1
        return String(os.path.join(self.compilation_dir, node.target.get_filename()))
