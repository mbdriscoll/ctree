"""
A set of basic transformers for python asts
"""
import os
import ast

from ctypes import c_long, c_int, c_uint, c_byte, c_ulong, c_ushort, c_short, c_wchar_p, c_char_p, c_float

from ctree.nodes import Project, CtreeNode
from ctree.c.nodes import Op, Constant, String, SymbolRef, BinaryOp, TernaryOp, Return, While, MultiNode
from ctree.c.nodes import If, CFile, FunctionCall, FunctionDecl, For, Assign, AugAssign, ArrayRef, Literal
from ctree.c.nodes import Lt, Gt, AddAssign, SubAssign, MulAssign, DivAssign, BitAndAssign, BitShRAssign, BitShLAssign
from ctree.c.nodes import BitOrAssign, BitXorAssign, ModAssign, Break, Continue, Pass, Array

from ctree.c.nodes import Op

from ctree.types import get_ctype

from ctree.visitors import NodeTransformer
from ctree.util import flatten


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
    def __init__(self,names_dict={}, constants_dict={}):
        self.names_dict = names_dict
        self.constants_dict =constants_dict

    PY_OP_TO_CTREE_OP = {
        ast.Add: Op.Add,
        ast.Mod: Op.Mod,
        ast.Mult: Op.Mul,
        ast.Sub: Op.Sub,
        ast.Div: Op.Div,
        ast.Lt: Op.Lt,
        ast.Gt: Op.Gt,
        ast.LtE: Op.LtE,
        ast.GtE: Op.GtE,
        ast.BitAnd: Op.BitAnd,
        ast.BitOr: Op.BitOr,
        ast.Eq: Op.Eq,
        ast.NotEq: Op.NotEq,
        ast.Not: Op.Not,
        ast.And: Op.And,
        ast.Or: Op.Or,
        ast.BitXor: Op.BitXor,
        ast.LShift: Op.BitShL,
        ast.RShift: Op.BitShR,
        ast.Is: Op.Eq,
        ast.IsNot: Op. NotEq
        # TODO list the rest
    }

    def visit_Num(self, node):
        return Constant(node.n)

    def visit_Str(self, node):
        return String(node.s)

    def visit_Name(self, node):
        if node.id in self.constants_dict:
            return Constant(self.constants_dict[node.id])
        if node.id in self.names_dict:
            return SymbolRef(self.names_dict[node.id])
        return SymbolRef(node.id)

    def visit_BinOp(self, node):
        lhs = self.visit(node.left)
        rhs = self.visit(node.right)
        op = self.PY_OP_TO_CTREE_OP.get(type(node.op), type(node.op))()
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
           node.iter.func.id in ('range', 'xrange'):
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



            #check no-op conditions.
            if all(isinstance(item, Constant) for item in (start, stop, step)):
                if step.value == 0:
                    raise ValueError("range() step argument must not be zero")
                if start.value == stop.value or \
                        (start.value < stop.value and step.value < 0) or \
                        (start.value > stop.value and step.value > 0):
                    return None

            # TODO allow any expressions castable to Long type
            target_type = c_long
            for el in (stop, start, step):
                if hasattr(el, 'get_type'): #typed item to try and guess type off of. Imperfect right now.
                    # TODO take the proper class instead of the last; if start, end are doubles, but step is long, target is double
                    t = el.get_type()
                    assert any(isinstance(t, klass) for klass in [
                        c_byte, c_int, c_long, c_short
                    ]), "Can only convert ranges with integer/long start/stop/step values"
                    target_type = t

            target = SymbolRef(node.target.id, target_type)
            op = Lt
            if hasattr(start,'value') and hasattr(stop,'value'):
                if start.value > stop.value:
                    op = Gt
            for_loop = For(
                Assign(target, start),
                op(target.copy(), stop),
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

        op = self.PY_OP_TO_CTREE_OP.get(type(node.ops[0]),type(node.ops[0]))()
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
        elif op is ast.BitXor:
            return BitXorAssign(target, value)
        elif op is ast.BitAnd:
            return BitAndAssign(target, value)
        elif op is ast.BitOr:
            return BitOrAssign(target, value)
        elif op is ast.Mod:
            return ModAssign(target, value)
        elif op is ast.LShift:
            return BitShLAssign(target, value)
        elif op is ast.RShift:
            return BitShRAssign(target, value)
        # TODO: Error?
        return node

    def visit_Assign(self, node):
        target_value_list = []
        #a = b -> targets = [ast.Name], value = ast.Name
        #a = b = c... -> targets = [ast.Name, ast.Name....], value = ast.Name
        if all(isinstance(i, ast.Name) for i in node.targets):
            target_value_list.extend((target, node.value) for target in node.targets)

        #a, b = c,d -> targets = [ast.Tuple], value = ast.Tuple
        elif isinstance(node.targets[0], (ast.List, ast.Tuple)):
            target_value_list.extend((target, value) for target, value in zip(node.targets[0].elts, node.value.elts))

        else:
            return node

        target_value_list = [(self.visit(target), self.visit(value)) for target, value in target_value_list]

        #making a multinode no matter what. It's cleaner than branching a lot
        body = []
        for target, value in target_value_list[:]:
            if isinstance(value, Constant):
                body.append(Assign(target, value))
                target_value_list.remove((target,value))

        new_targets = []
        for target, value in target_value_list:
            #making temporary variables for results.
            new_target = target.copy()
            new_target.name = "____temp__" + new_target.name
            new_targets.append(new_target)
            body.append(Assign(new_target, target))

        for new_target, (target, value) in zip(new_targets, target_value_list):
            body.append(Assign(new_target.copy(), value))

        for new_target, (target, value) in zip(new_targets, target_value_list):
            #now assigning the temp values to the original variables
            body.append(Assign(target, new_target.copy()))
        return MultiNode(body = body)


        # if isinstance(node.targets[0], ast.Name): #single assign
        #     target = self.visit(node.targets[0])
        #     value = self.visit(node.value)
        #     return Assign(target, value)
        # elif isinstance(node.targets[0], ast.Tuple) or isinstance(node.targets[0], ast.List):
        #     body = []
        #     temp_var_map = {}
        #     for target, value in zip(node.targets[0].elts, node.value.elts):
        #         # TODO: might need to do some DeclarationFiller thing here to get the types of the new ____temp_variables.
        #
        #         temp_target_id = "____temp__" + value.id
        #         temp_target = ast.Name(id = temp_target_id, ctx = target.ctx)
        #         temp_var_map[temp_target] = target
        #
        #         ref = self.visit(temp_target)
        #         # ref.type = c_float()# TODO: need to change this from c_float() to whatever the value's type is using DeclarationFiller.
        #
        #         body.append(
        #             Assign(ref, self.visit(value))
        #         )
        #     for temp_target, target in temp_var_map.iteritems():
        #         body.append(
        #             Assign(self.visit(target), self.visit(temp_target))
        #         )
        #     return MultiNode(body)
        # return node

    def visit_Subscript(self, node):
        if isinstance(node.slice,ast.Index):
            value = self.visit(node.value)
            index = self.visit(node.slice.value)
            return ArrayRef(value,index)
        else:
            return node

    def visit_While(self,node):
        cond = self.visit(node.test)
        body = [self.visit(i) for i in node.body]
        return While(cond, body)

    def visit_Lambda(self, node):

        if isinstance(node, ast.Lambda):
            def_node = ast.FunctionDef(name = "default", args = node.args, body = node.body, decorator_list = None)

            params = [self.visit(p) for p in def_node.args.args]
            defn = [Return(self.visit(def_node.body))]
            decl_node = FunctionDecl(None, def_node.name, params, defn)
            Lifter().visit_FunctionDecl(decl_node)

            return decl_node
        else:
            return node

    def visit_Break(self, node):
        return Break()

    def visit_Continue(self, node):
        return Continue()

    def visit_Pass(self, node):
        return Pass()

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


class Lifter(NodeTransformer):
    """
    To aid in adding new includes or parameters during tree
    traversals, users can store them with arbitrary child nodes and call this
    transformation to move them to the correct position.
    """
    def __init__(self, lift_params=True, lift_includes=True):
        self.lift_params = lift_params
        self.lift_includes = lift_includes

    def visit_FunctionDecl(self, node):
        if self.lift_params:
            for child in ast.walk(node):
                for param in getattr(child, '_lift_params', []):
                    if param not in node.params:
                        node.params.append(param)
                    #del child._lift_params
        return self.generic_visit(node)

    def visit_CFile(self, node):
        if self.lift_includes:
            new_includes = []
            for child in ast.walk(node):
                for include in getattr(child, '_lift_includes', []):
                    if include not in new_includes:
                        new_includes.append(include)
            node.body = list(new_includes) + node.body
        return self.generic_visit(node)

class DeclarationFiller(NodeTransformer):
    def __init__(self):
        self.__environments = [{}]

    def __lookup(self, key):
        """
        :param key:
        :return: Looks up the last value corresponding to key in self.__environments
        """
        value = sentinel = object()
        for environment in self.__environments:
            if key in environment:
                value = environment[key]
        if value is sentinel:
            raise KeyError('Did not find {} in environments'.format(repr(key)))
        return value

    def __add_entry(self, key, value):
        self.__environments[-1][key] = value

    def __add_environment(self):
        self.__environments.append({})

    def __pop_environment(self):
        return self.__environments.pop()


    def visit_FunctionDecl(self, node):
        #add current FunctionDecl's return type onto environments
        self.__add_entry(node.name, node.return_type)
        #new environment every time we enter a function
        self.__add_environment()
        for param in node.params:
            #binding types of parameters
            self.__add_entry(param.name, param.type)
        node.defn = [self.visit(i) for i in node.defn]
        self.__pop_environment()
        return node

    def visit_SymbolRef(self, node):
        if node.type:
            self.__add_entry(node.name, node.type)
        return node

    def visit_BinaryOp(self, node):
        if isinstance(node.op, Op.Assign):
            node.left = self.visit(node.left)
            if isinstance(node.left, BinaryOp):
                return node
            node.right = self.visit(node.right)
            name = node.left
            value = node.right
            if hasattr(node.left, 'type'):
                return node
            try:
                self.__lookup(name.name)
            except KeyError:
                if hasattr(value, 'get_type'):
                    node.left.type = value.get_type()
                elif isinstance(value, String):
                    node.left.type = c_char_p()
                elif isinstance(value, SymbolRef):
                    node.left.type = self.__lookup(value.name)

                self.__add_entry(node.left.name, node.left.type)
        return node

