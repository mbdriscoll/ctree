"""
A set of basic transformers for python asts
"""
import os
import sys
import ast
from ctypes import c_long, c_int, c_byte, c_short, c_char_p, c_void_p
import ctypes
from collections import deque

import ctree
from ctree.nodes import Project
from ctree.c.nodes import Constant, String, SymbolRef, BinaryOp, TernaryOp, Return, While, MultiNode, UnaryOp
from ctree.c.nodes import If, CFile, FunctionCall, FunctionDecl, For, Assign, ArrayRef
from ctree.c.nodes import Lt, Gt, AddAssign, SubAssign, MulAssign, DivAssign, BitAndAssign, BitShRAssign, BitShLAssign
from ctree.c.nodes import BitOrAssign, BitXorAssign, ModAssign, Break, Continue, Pass, Array, Literal
from ctree.c.nodes import Op
from ctree.visitors import NodeTransformer

from ctree.types import get_ctype, get_common_ctype


#conditional imports

if sys.version_info < (3,0):
    from itertools import izip_longest
else:
    from itertools import zip_longest as izip_longest

def get_type(node):
    if hasattr(node, 'get_type'):
        return type(node.get_type())
    elif hasattr(node, 'type'):
        return type(node.type)
    return c_void_p

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
        ast.IsNot: Op.NotEq,
        ast.USub:Op.SubUnary,
        ast.UAdd:Op.AddUnary,
        # TODO list the rest
    }

    PY_UOP_TO_CTREE_UOP = {
        'UAdd': Op.Add,
        'USub': Op.Sub,
        'Not': Op.Not,
        'Invert': Op.BitNot
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

    def visit_UnaryOp(self, node):
        op = self.PY_UOP_TO_CTREE_UOP[node.op.__class__.__name__]()
        operand = self.visit(node.operand)
        return UnaryOp(op, operand)

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
            target_types = [c_long]
            for el in (stop, start, step):
                if hasattr(el, 'get_type'): #typed item to try and guess type off of. Imperfect right now.
                    # TODO take the proper class instead of the last; if start, end are doubles, but step is long, target is double
                    t = el.get_type()
                    assert any(isinstance(t, klass) for klass in [
                        c_byte, c_int, c_long, c_short
                    ]), "Can only convert ranges with integer/long start/stop/step values"
                    target_types.append(type(t))
            target_type = get_common_ctype(target_types)()

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
        # if op is ast.Add:
        #     return AddAssign(target, value)
        # elif op is ast.Sub:
        #     return SubAssign(target, value)
        # elif op is ast.Mult:
        #     return MulAssign(target, value)
        # elif op is ast.Div:
        #     return DivAssign(target, value)
        # elif op is ast.BitXor:
        #     return BitXorAssign(target, value)
        # # TODO: Error?
        lookup = {
            ast.Add: 'AddAssign', ast.Sub: 'SubAssign', ast.Mult: 'MulAssign', ast.Div: 'DivAssign',
            ast.BitAnd: 'BitAndAssign', ast.BitOr: 'BitOrAssign', ast.BitXor: 'BitXorAssign',
            ast.LShift: 'BitShLAssign', ast.RShift: 'BitShRAssign'
        }
        if op in lookup:
            return getattr(ctree.c.nodes, lookup[op])(target, value)
        return node

    def visit_Assign(self, node):

        def parse_pairs(node):
            def targets_to_list(targets): #parses target into nested lists
                res = []
                for elt in targets:
                    if not isinstance(elt, (ast.List, ast.Tuple)):
                        res.append(elt)
                    elif isinstance(elt, (ast.Tuple, ast.List)):
                        res.append(targets_to_list(elt.elts))
                return res

            def value_to_list(value): #parses value into nested lists for multiple assign
                res = []
                if not isinstance(value, (ast.List, ast.Tuple)):
                    return value
                for elt in value.elts:
                    if not isinstance(value, (ast.List, ast.Tuple)):
                        res.append(elt)
                    else:
                        res.append(value_to_list(elt))
                return ast.List(elts=res)

            def pair_lists(targets, values):
                res = []
                queue = deque((target, values) for target in targets)
                sentinel = object()
                while queue:
                    target, value = queue.popleft()
                    if isinstance(target, list):
                        #target hasn't been completely unrolled yet
                        for sub_target, sub_value in izip_longest(target, value.elts, fillvalue=sentinel):
                            if sub_target is sentinel or sub_value is sentinel:
                                raise ValueError('Incorrect number of values to unpack')
                            queue.append((sub_target, sub_value))
                    else:
                        res.append((target, value))
                return res

            targets = targets_to_list(node.targets)
            values = value_to_list(node.value)
            return pair_lists(targets, values)


        target_value_list = [(self.visit(target), self.visit(value)) for target, value in parse_pairs(node)]

        # making a multinode no matter what. It's cleaner than branching a lot
        operation_body = []
        swap_body = []
        for target, value in target_value_list:
            if not isinstance(target, SymbolRef):
                operation_body.append(Assign(target, value))
                continue
            if isinstance(value, Literal) and not isinstance(value, SymbolRef):
                operation_body.append(Assign(target, value))
                continue
            new_target = target.copy()
            new_target.name = "____temp__" + new_target.name
            operation_body.append(Assign(new_target, value))
            swap_body.append(Assign(target, new_target.copy()))
        return MultiNode(body=operation_body + swap_body)


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
            def_node = ast.FunctionDef(name="default", args=node.args, body=node.body, decorator_list=None)

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

    def visit_List(self, node):
        elts = [self.visit(elt) for elt in node.elts]
        types = [get_type(elt) for elt in elts]
        array_type = get_common_ctype(types)
        return Array(type=ctypes.POINTER(array_type)(), body=elts)

    def visit_UnaryOp(self, node):
        argument = self.visit(node.operand)
        op = self.PY_OP_TO_CTREE_OP.get(type(node.op), type(node.op))()
        return UnaryOp(op, argument)

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
        if isinstance(key, SymbolRef):
            key = key.name
        value = sentinel = object()
        for environment in self.__environments:
            if key in environment:
                value = environment[key]
        if value is sentinel:
            raise KeyError('Did not find {} in environments'.format(repr(key)))
        return value

    def __has_key(self, key):
        try:
            self.__lookup(key)
            return True
        except KeyError:
            return False

    def __add_entry(self, key, value):
        if isinstance(key, SymbolRef):
            key = key.name
        self.__environments[-1][key] = value

    def __add_environment(self):
        self.__environments.append({})

    def __pop_environment(self):
        return self.__environments.pop()

    def visit_FunctionDecl(self, node):
        # add current FunctionDecl's return type onto environments
        self.__add_entry(node.name, node.return_type)

        # new environment every time we enter a function
        self.__add_environment()

        for param in node.params:
            # binding types of parameters
            self.__add_entry(param.name, param.type)

        node.defn = [self.visit(i) for i in node.defn]
        self.__pop_environment()
        return node

    def visit_SymbolRef(self, node):

        if node.type:
            self.__add_entry(node.name, node.type)
        return node

    def visit_FunctionCall(self, node):
        if self.__has_key(node.func):
            node.type = self.__lookup(node.func)
        node.args = [self.visit(arg) for arg in node.args]
        return node

    def visit_BinaryOp(self, node):
        if isinstance(node.op, Op.Assign):
            node.left = self.visit(node.left)
            if isinstance(node.left, BinaryOp):
                return node
            node.right = self.visit(node.right)
            name = node.left
            value = node.right
            if hasattr(name, 'type') and name.type is not None:
                return node
            if hasattr(name, 'name') and not self.__has_key(name.name):
                if name.name.startswith('____temp__'):                  # temporary variable types can be derived from the variables that they represent
                    stripped_name = name.name.lstrip('____temp__')
                    if self.__has_key(stripped_name):
                        node.left.type = self.__lookup(stripped_name)

                elif hasattr(value, 'get_type'):
                    node.left.type = value.get_type()
                elif isinstance(value, String):
                    node.left.type = c_char_p()
                elif isinstance(value, SymbolRef):
                    node.left.type = self.__lookup(value.name)
                elif isinstance(value, FunctionCall):
                    if self.__has_key(value.func):
                        node.left.type = self.__lookup(value.func)

                self.__add_entry(node.left.name, node.left.type)
        return node

