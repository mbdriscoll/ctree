"""
Code generator for the expression A*(B+C), where A, B, and C are vectors
and all operations are element-wise.
"""

n = 0

import itertools
import logging
import copy

logging.basicConfig(level=20)

import numpy as np
import pycl as cl
from ctypes import *

import ctree.np
import ctree.ocl

from ctree.frontend import get_ast
from ctree.c.nodes import *
from ctree.cpp.nodes import *
from ctree.omp.macros import *
from ctree.ocl.macros import *
from ctree.templates.nodes import *
from ctree.transformations import *
from ctree.visitors import NodeVisitor
from ctree.jit import LazySpecializedFunction
from ctree.jit import ConcreteSpecializedFunction


# ---------------------------------------------------------------------------
# Specializer code - nodes

class Vector(CtreeNode):
    def __init__(self, name, type=None, loc=None):
        self.name = name
        self.loc = loc
        self.type = type
        self._loc_cache = {}

    def label(self):
        return "name: %s\\nloc: %s\\ntype: %s" % \
            (self.name, self.loc, self.type)

    def get_type(self):
        return self.type

    def codegen(self, indent=0):
        return "%s %s" % (self.get_type(), self.name)

    def copy_to(self, mem):
        if mem not in self._loc_cache:
            self._loc_cache[mem] = CopiedVector(self, to=mem, type=self.type)
        return self._loc_cache[mem]

class CopiedVector(Vector):
    _fields = ["data"]
    _next_id = 0
    def __init__(self, data=None, to=None):
        self.data = data
        name = "copied%d" % self._next_id
        CopiedVector._next_id += 1
        super(CopiedVector, self).__init__(name=name, loc=to)

    def label(self):
        to = "to: %s" % self.loc
        frm = "from: %s" % getattr(self.data, 'loc', '?')
        ty = "type: %s" % getattr(self, 'type', '?')
        return "name: %s\\n%s\\n%s\\n%s" % (self.name, to, frm, ty)


class ComputedVector(Vector):
    _fields = ["data"]
    _next_id = 0
    def __init__(self, data=None, name=None, loc=None):
        self.data = data
        if not name:
            name = "computed%d" % self._next_id
            ComputedVector._next_id += 1
        super(ComputedVector, self).__init__(name=name, loc=loc)

# ---------------------------------------------------------------------------
# Specializer code - transformers

class ApplyDistributiveProperty(NodeTransformer):
    def __init__(self, directives):
        super(ApplyDistributiveProperty, self).__init__()
        self._directives = iter(directives)

    def visit_BinaryOp(self, node):
        ab = node.left  = self.visit(node.left)
        cd = node.right = self.visit(node.right)
        dist_left  = isinstance(ab, BinaryOp) and isinstance(ab.op, Op.Add)
        dist_right = isinstance(cd, BinaryOp) and isinstance(cd.op, Op.Add)
        if isinstance(node.op, Op.Mul):
            if dist_right and self._directives.next():
                c, d = cd.left, cd.right
                abc = self.visit( Mul(ab,c) )
                abd = self.visit( Mul(ab,d) )
                return Add(abc, abd)
            elif dist_left and self._directives.next():
                a, b = ab.left, ab.right
                acd = self.visit( Mul(a, cd) )
                bcd = self.visit( Mul(b, cd) )
                return Add(acd, bcd)
        return node

class VectorFinder(NodeTransformer):
    def __init__(self, types, main_memory):
        self._cache = {}
        self._types = (ty() for ty in types)
        self._main_memory = main_memory

    def visit_SymbolRef(self, node):
        return self._cache[node.name]

    def visit_FunctionDecl(self, node):
        for param in node.params:
            self._cache[param.name] = Vector(param.name, self._types.next(), loc=self._main_memory)
        return self.generic_visit(node)


class InsertIntermediates(NodeTransformer):
    def __init__(self, main_memory, locs):
        self._main_memory = main_memory
        self._locs = iter(locs)

    def visit_BinaryOp(self, node):
        tree = self.generic_visit(node)
        loc = self._locs.next()
        return ComputedVector(tree, loc=loc)

    def visit_Return(self, node):
        answer = self.visit(node.value)
        answer.name = "answer"
        answer.loc = self._main_memory
        return answer


class LocationTagger(NodeTransformer):
    def __init__(self, locs):
        self._locs = iter(locs)

    def visit_ComputedVector(self, node):
        node.loc = self._locs.next()
        return self.generic_visit(node)


class DoFusion(NodeTransformer):
    def __init__(self, directives):
        self._directives = iter(directives)

    def visit_BinaryOp(self, node):
        tree = self.generic_visit(node)
        if isinstance(tree.left, ComputedVector) and self._directives.next():
            tree.left = tree.left.data
        if isinstance(tree.right, ComputedVector) and self._directives.next():
            tree.right = tree.right.data
        return tree


class CopyInserter(NodeTransformer):
    def __init__(self, main_memory):
        self._locs = [main_memory]

    def visit_ComputedVector(self, node):
        outer_loc = self._locs[-1]
        self._locs.append(node.loc)
        self.generic_visit(node)
        if node.loc != outer_loc:
            node = CopiedVector(data=node, to=outer_loc)
        self._locs.pop()
        return node


class AllocateIntermediates(NodeTransformer):
    def __init__(self, dtype, length):
        self.dtype = dtype
        self.length = length

    def visit_ComputedVector(self, node):
        node.mem, ty = node.loc.allocate(self.length, self.dtype)
        node.lift(params=[(SymbolRef(node.name, ty), node.mem)])
        node.type = ty
        return self.generic_visit(node)

    def visit_CopiedVector(self, node):
        node.mem, ty = node.loc.allocate(self.length, self.dtype)
        node.lift(params=[(SymbolRef(node.name, ty), node.mem)])
        node.type = ty
        return self.generic_visit(node)


class GetWorkItems(NodeVisitor):
    def visit_BinaryOp(self, node):
        lhs = self.visit(node.left)
        rhs = self.visit(node.right)
        return lhs + rhs

    def visit_ComputedVector(self, node):
        return [node]

class FindParallelism(NodeVisitor):
    def visit_BinaryOp(self, node):
        left  = self.visit(node.left)
        right = self.visit(node.right)
        if left and right:
            return {left, right}
        elif left or right:
            return left or right

    def visit_ComputedVector(self, node):
        compute = self.visit(node.data)
        if compute:
            return [compute, node]
        else:
            return node

    def visit_CopiedVector(self, node):
        copyin = self.visit(node.data)
        if copyin:
            return [copyin, node]
        else:
            return node

    def visit_FunctionDecl(self, node):
        return [self.visit(stmt) for stmt in node.defn]


class RefConverter(NodeTransformer):
    class ToArrayRef(NodeTransformer):
        def visit_ComputedVector(self, node):
            return ArrayRef(SymbolRef(node.name), SymbolRef("i"))
        def visit_CopiedVector(self, node):
            return ArrayRef(SymbolRef(node.name), SymbolRef("i"))
        def visit_Vector(self, node):
            return ArrayRef(SymbolRef(node.name), SymbolRef("i"))

    class ToParamDecl(NodeTransformer):
        def visit_Vector(self, node):
            return SymbolRef(node.name, node.type)

    def visit_ComputedVector(self, node):
        node.data = RefConverter.ToArrayRef().visit(node.data)
        return node

    def visit_FunctionDecl(self, node):
        param_conv = RefConverter.ToParamDecl()
        node.params = [param_conv.visit(p) for p in node.params]
        node.defn = [self.visit(stmt) for stmt in node.defn]
        return node


class KernelCall(CtreeNode):
    _fields = ['args', 'kernel']
    def __init__(self, name=None, args=None, kernel=None):
        self.name = name
        self.args = args or []
        self.kernel = kernel


class KernelOutliner(NodeTransformer):
    _next_kernel_id = 0
    def __init__(self, context, dev_mem, queue):
        self.context = context
        self.dev_memory = dev_mem
        self.queue = queue

    def visit_ComputedVector(self, node):
        if node.loc == self.dev_memory:
            print "LOC"
            name = "outline%d" % KernelOutliner._next_kernel_id
            KernelOutliner._next_kernel_id += 1
            return outline(node.data, name=name)
        else:
            return node


class LowerCopies(NodeTransformer):
    def __init__(self, length, dtype, main_mem, device_mem, queue):
        self.nBytes = length * dtype.itemsize
        self.main_mem = main_mem
        self.device_mem = device_mem
        self.queue = queue

    def visit_CopiedVector(self, node):
        dst = node
        src = node.data
        assert src != dst, "Found a copy within same memory space."

        if src.loc == self.main_mem and dst.loc == self.device_mem:
            # host to device
            call = clEnqueueWriteBuffer(self.queue.copy(), dst.name, True, 0, self.nBytes, src.name)
        else:
            # device to host
            call = clEnqueueReadBuffer(self.queue.copy(), src.name, True, 0, self.nBytes, dst.name)

        assert dst.type is not None, str(dst)
        call.lift(params=[(SymbolRef(dst.name, dst.type), dst.mem)])

        return call

def outline(tree, name="outlined"):

    class SymRefGatherer(NodeTransformer):
        def __init__(self):
            self.signature = []
            self.declared = set()

        def visit_SymbolRef(self, node):
            if node.type or node.name == "i": # FIXME
                self.declared.add(node.name)
            elif node not in self.signature and \
                 node.name not in self.declared:
                self.signature.append(node)
            return node

    symref_gatherer = SymRefGatherer()
    tree = symref_gatherer.visit(tree)
    signature = symref_gatherer.signature

    if not isinstance(tree, list):
        tree = [tree]

    fn = FunctionDecl(None, name, signature, tree).set_kernel()
    return KernelCall(name, signature, fn)



class Loopize(NodeTransformer):
    def __init__(self, nElems):
        self.nElems = nElems

    def visit_ComputedVector(self, node):
        i = SymbolRef("i", c_int())
        for_stmt = For(Assign(i, Constant(0)),
                       Lt(i.copy(), Constant(self.nElems)),
                       PostInc(i.copy()), [
            Assign( ArrayRef(SymbolRef(node.name), i.copy()),
                    self.visit(node.data) )
        ])

        for_stmt._lift_params = node._lift_params

        return [CppComment("on %s" % node.loc), for_stmt]


class ArgZipper(NodeTransformer):
    def visit_FunctionDecl(self, node):
        self.extra_args = []
        def process(elem):
            if isinstance(elem, tuple):
                sym, val = elem
                self.extra_args.append(val)
                if sym.name == 'answer':
                    self.answer = val
                return sym
            else:
                return elem
        node.params = [process(e) for e in node.params]
        return node


class Memory(object):
    pass

class MainMemory(Memory):
    def allocate(self, length, dtype):
        ty = np.ctypeslib.ndpointer(dtype)()
        mem = np.empty([length], dtype=dtype)
        return mem, ty

    def __str__(self):
        return "MainMemory"

class OclMemory(Memory):
    def __init__(self, context):
        self.context = context

    def allocate(self, length, dtype):
        mem = cl.clCreateBuffer(self.context, length * dtype.itemsize)
        ty = mem
        return mem, ty

    def __str__(self):
        return "OclMemory<%s>" % [dev.name for dev in self.context.devices][0]

# ---------------------------------------------------------------------------
# Specializer code - translator

class OpTranslator(LazySpecializedFunction):
    def get_tuning_driver(self):
        from ctree.tune import BruteForceTuningDriver
        from ctree.tune import MinimizeTime
        from ctree.tune import IntegerParameter
        from ctree.tune import BooleanArrayParameter
        from ctree.tune import IntegerArrayParameter

        nMemorySpaces = 1 + len(cl.clGetDeviceIDs())

        params = [
            IntegerArrayParameter("locs", count=3, lower_bound=0, upper_bound=nMemorySpaces),
            BooleanArrayParameter("fusion", count=2),
            BooleanArrayParameter("distribute", count=1),
        ]

        return BruteForceTuningDriver(params, MinimizeTime())

    def args_to_subconfig(self, args):
        """
        Analyze arguments and return a 'subconfig', a hashable object
        that classifies them. Arguments with identical subconfigs
        might be processed by the same generated code.
        """
        ptrs = tuple(np.ctypeslib.ndpointer(a.dtype) for a in args)
        return {
            'ptrs': ptrs,
            'len': len(args[0]),
        }

    def transform(self, py_ast, program_config):
        """
        Convert the Python AST to a C AST according to the directions
        given in program_config.
        """
        arg_config, tuner_config = program_config

        # set up OpenCL context and memory spaces
        import pycl
        context = pycl.clCreateContextFromType(pycl.CL_DEVICE_TYPE_ALL)
        queues = [pycl.clCreateCommandQueue(context, dev) for dev in context.devices]
        c_func = ElementwiseFunction(context, queues)

        memories = [MainMemory()] + [OclMemory(q) for q in queues]
        main_memory = memories[0]


        # pull stuff out of autotuner
        distribute_directives = tuner_config['distribute']
        locs = [memories[loc] for loc in tuner_config['locs']]
        fusion_directives = tuner_config['fusion']

        with open('graph.00.dot', 'w') as f: f.write(py_ast.to_dot())

        # run basic conversions
        proj = PyBasicConversions().visit(py_ast)
        with open('graph.01.dot', 'w') as f: f.write(proj.to_dot())

        # run platform-independent transformations
        proj = ApplyDistributiveProperty(distribute_directives).visit(proj)
        with open('graph.02.dot', 'w') as f: f.write(proj.to_dot())

        # set parameter types
        ptrs = arg_config['ptrs']
        proj = VectorFinder(ptrs, main_memory).visit(proj)
        with open('graph.03.dot', 'w') as f: f.write(proj.to_dot())

        proj = InsertIntermediates(main_memory, locs).visit(proj)
        with open('graph.04.dot', 'w') as f: f.write(proj.to_dot())

        proj = CopyInserter(main_memory).visit(proj)
        with open('graph.05.dot', 'w') as f: f.write(proj.to_dot())

        proj = DoFusion(fusion_directives).visit(proj)
        with open('graph.06.dot', 'w') as f: f.write(proj.to_dot())

        dtype, length = ptrs[0]._dtype_, arg_config['len']
        proj = AllocateIntermediates(dtype, length).visit(proj)
        with open('graph.07.dot', 'w') as f: f.write(proj.to_dot())

        py_op = proj.find(FunctionDecl, name="py_op")
        schedules = FindParallelism().visit(py_op)
        py_op.defn = parallelize_tasks(schedules)
        with open('graph.08.dot', 'w') as f: f.write(proj.to_dot())

        proj = RefConverter().visit(proj)
        with open('graph.09.dot', 'w') as f: f.write(proj.to_dot())

        #proj = LowerCopies(length, dtype, main_memory, dev_memory, queue.copy()).visit(proj)
        #with open('graph.10.dot', 'w') as f: f.write(proj.to_dot())

        proj = Loopize(length).visit(proj)
        with open('graph.11.dot', 'w') as f: f.write(proj.to_dot())

        zipper = ArgZipper()
        proj = zipper.visit( Lifter().visit(proj) )
        c_func.extra_args = zipper.extra_args
        c_func.answer = zipper.answer
        with open('graph.12.dot', 'w') as f: f.write(proj.to_dot())

        """

        assert isinstance(fn.defn[0], Vector)

        import pycl

        context = SymbolRef("context", pycl.cl_context())
        queue = SymbolRef("queue", pycl.cl_command_queue())



        proj = KernelOutliner(context, dev_memory, queue).visit(proj)

        proj = RefConverter().visit(proj)
        proj.find(CFile).body.insert(0, CppInclude("OpenCL/OpenCL.h"))

        nUserArgs = len(ptrs)
        fn = proj.find(FunctionDecl)
        fn.params[nUserArgs:], extra_args = zip(*fn.params[nUserArgs:])
        fn.params += [context, queue]
        c_func.extra_args = list(extra_args) + [c_func.context, c_func.queue]

        global n
        with open('graph.%d.dot' % n, 'w') as f:
            f.write(proj.to_dot())
        n += 1
        """

        fn = proj.find(FunctionDecl)
        return c_func.finalize("py_op", proj, fn.get_type())

class ElementwiseFunction(ConcreteSpecializedFunction):
    def __init__(self, context, queues):
        self.context = context
        self.queues = queues

    def finalize(self, entry_name, proj, typesig):
        self._c_function = self._compile(entry_name, proj, typesig)
        return self

    def __call__(self, *args):
        full_args = list(args) + self.extra_args
        self._c_function(*full_args)
        return np.copy(self.answer)


class Elementwise(object):
    """
    A class for managing independent operation on elements
    in numpy arrays.
    """

    def __init__(self, fn):
        """Instantiate translator."""
        self.jit = OpTranslator(get_ast(fn))

    def __call__(self, *args):
        """Apply the operator to the arguments via a generated function."""
        return self.jit(*args)


# ---------------------------------------------------------------------------
# User code

def py_op(a, b, c):
    return a * (b + c)

def main():
    n = 12
    c_op = Elementwise(py_op)

    # doubling doubles
    for i in range(160):
      a = np.arange(0*n, 1*n, dtype=np.float32())
      b = np.arange(1*n, 2*n, dtype=np.float32())
      c = np.arange(2*n, 3*n, dtype=np.float32())
      d = np.arange(3*n, 4*n, dtype=np.float32())

      actual = c_op(a, b, c)
      expected = py_op(a, b, c)

      np.testing.assert_array_equal(actual, expected)

    print("Success.")


if __name__ == '__main__':
    main()
