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
    def __init__(self, main_memory):
        self._main_memory = main_memory

    def visit_BinaryOp(self, node):
        tree = self.generic_visit(node)
        return ComputedVector(tree, loc=node.loc)

    def visit_Return(self, node):
        answer = self.visit(node.value)
        answer.name = "answer"
        answer.loc = self._main_memory
        return answer

    class AssertHasAllIntermediates(NodeVisitor):
        def visit_BinaryOp(self, node):
            assert not isinstance(node.left, BinaryOp)
            assert not isinstance(node.right, BinaryOp)
            self.generic_visit(node)

    def visit(self, node):
        proj = super(InsertIntermediates, self).visit(node)
        InsertIntermediates.AssertHasAllIntermediates().visit(proj)
        return proj

BinaryOp.label = lambda self: "loc: %s" % getattr(self, 'loc', '?')

class LocationTagger(NodeTransformer):
    def __init__(self, locs):
        self._locs = iter(locs)

    def visit_BinaryOp(self, node):
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

    def visit_Vector(self, node):
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
        node.mem, sym = node.loc.allocate(self.length, self.dtype, node.name)
        node.lift(params=[(sym, node.mem)])
        node.type = sym.type
        return self.generic_visit(node)

    def visit_CopiedVector(self, node):
        node.mem, sym = node.loc.allocate(self.length, self.dtype, node.name)
        node.lift(params=[(sym, node.mem)])
        node.type = sym.type
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
            return frozenset([left, right])
        elif left or right:
            return left or right

    def visit_ComputedVector(self, node):
        compute = self.visit(node.data)
        if compute:
            return (compute, node)
        else:
            return node

    def visit_CopiedVector(self, node):
        copyin = self.visit(node.data)
        if copyin:
            return (copyin, node)
        else:
            return node

    def visit_FunctionDecl(self, node):
        return tuple(self.visit(stmt) for stmt in node.defn)


class RefConverter(NodeTransformer):
    class ToParamDecl(NodeTransformer):
        def visit_Vector(self, node):
            return SymbolRef(node.name, node.type)
        def visit_ComputedVector(self, node):
            return SymbolRef(node.name, node.type)
        def visit_CopiedVector(self, node):
            return SymbolRef(node.name, node.type)

    def visit_BinaryOp(self, node):
        if isinstance(node.left, Vector):
            node.left = ArrayRef(SymbolRef(node.left.name), SymbolRef("i"))
        if isinstance(node.right, Vector):
            node.right = ArrayRef(SymbolRef(node.right.name), SymbolRef("i"))
        return self.generic_visit(node)

    def visit_FunctionDecl(self, node):
        param_conv = RefConverter.ToParamDecl()
        node.params = [param_conv.visit(p) for p in node.params]
        node.defn = [self.visit(stmt) for stmt in node.defn]
        return node


class KernelCall(CtreeNode):
    _fields = ['args', 'kernel', 'queue']
    def __init__(self, location=None, name=None, global_size=0, local_size=0, args=None, kernel=None):
        self.location = location
        self.name = name
        self.global_size = global_size
        self.local_size = local_size
        self.args = args
        self.kernel = kernel

        if isinstance(self.local_size, int):
            self.local_size = Constant(self.local_size)
        if isinstance(self.global_size, int):
            self.global_size = Constant(self.global_size)

    def label(self):
        return "name: %s" % self.name

class LowerKernelCalls(NodeTransformer):
    def visit_KernelCall(self, node):
        args = []
        for i, arg in enumerate(node.args):
            size = SizeOf(SymbolRef(arg.name))
            setter = clSetKernelArg(node.name, i, size, Ref(SymbolRef(arg.name)))
            args.append(setter)

        kernel_decl = SymbolRef(node.name, cl.cl_kernel())
        kernel_symbol = kernel_decl.copy()
        call = clEnqueueNDRangeKernel(node.location.symbol.copy(), kernel_symbol, work_dim=Constant(1), global_size=node.global_size, local_size=node.local_size)

        kernel = RefConverter().visit(node.kernel)
        for param in kernel.params:
            param.type = param.type.ptr_type
        kernel.defn.insert(0, Assign(SymbolRef("i", c_int()), get_global_id(0)))
        kernel_src = kernel.codegen()
        kernel_comment = CppComment(kernel_src)

        context = node.location.queue.context
        kernel_ptr = cl.clCreateProgramWithSource(context, kernel_src).build()[node.name]
        call.lift(params=[(kernel_decl, kernel_ptr)])

        return args + [call, kernel_comment]

def outline(tree, name="outlined"):
    class VecGatherer(NodeTransformer):
        def __init__(self):
            self.signature = []

        def visit_ComputedVector(self, node):
            if node not in self.signature:
                self.signature.append(node)
            return self.generic_visit(node)

        def visit_CopiedVector(self, node):
            if node not in self.signature:
                self.signature.append(node)
            return self.generic_visit(node)

    vec_gatherer = VecGatherer()
    tree = vec_gatherer.visit(tree)
    signature = vec_gatherer.signature

    if not isinstance(tree, list):
        tree = [tree]

    return FunctionDecl(None, name, signature, tree)


class KernelOutliner(NodeTransformer):
    def __init__(self, work_items):
        self.work_items = work_items

    def visit_ComputedVector(self, node):
        if isinstance(node.loc, OclMemory):
            fn = outline(Assign(node, node.data), "outline_%s" % node.name)
            call = KernelCall(node.loc, fn.name, self.work_items, 1, fn.params, fn.set_kernel())
            return call
        else:
            return node

    def visit_CopiedVector(self, node):
        return node


class LowerLoopsAndCopies(NodeTransformer):
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

    def visit_CopiedVector(self, node):
        dst = node
        src = node.data

        if isinstance(dst.loc, OclMemory): # host to device
            cl_node = dst
            queue_sym = dst.loc.symbol
            call = clEnqueueWriteBuffer(queue_sym.copy(), dst.name, True, 0, dst.type.size, src.name)
        elif isinstance(src.loc, OclMemory): # device to host
            cl_node = src
            queue_sym = src.loc.symbol
            call = clEnqueueReadBuffer(queue_sym.copy(), src.name, True, 0, src.type.size, dst.name)
        else:
            raise ValueError("Copy between non-ocl devices.")

        assert dst.type is not None, str(dst)

        params = [(cl_node.loc.symbol, cl_node.loc.queue)]
        if hasattr(dst, 'mem'):
            params.append((SymbolRef(dst.name, dst.type), dst.mem))
        if hasattr(src, 'mem'):
            params.append((SymbolRef(src.name, src.type), src.mem))

        call._lift_params = node._lift_params
        call.lift(
            includes=[CppInclude("OpenCL/OpenCL.h")],
            params=params
        )

        return call


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
    def allocate(self, length, dtype, name):
        ty = np.ctypeslib.ndpointer(dtype)()
        mem = np.empty([length], dtype=dtype)
        return mem, SymbolRef(name, ty)

    def __str__(self):
        return "MainMemory"

class OclMemory(Memory):
    _next_cq_id = 0
    def __init__(self, queue):
        self.queue = queue
        self.symbol = SymbolRef("queue%d" % self._next_cq_id, queue)
        self._next_cq_id += 1

    def allocate(self, length, dtype, name):
        mem = cl.clCreateBuffer(self.queue.context, length * dtype.itemsize)
        mem.ptr_type = np.ctypeslib.ndpointer(dtype)()
        mem.ptr_type._global = True
        return mem, SymbolRef(name, mem)

    def __str__(self):
        return "OclMemory<%s>" % self.queue.device

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
        ptrs = arg_config['ptrs']
        dtype, length = ptrs[0]._dtype_, arg_config['len']

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
        proj = VectorFinder(ptrs, main_memory).visit(proj)
        with open('graph.03.dot', 'w') as f: f.write(proj.to_dot())

        proj = LocationTagger(locs).visit(proj)
        with open('graph.04.dot', 'w') as f: f.write(proj.to_dot())

        proj = InsertIntermediates(main_memory).visit(proj)
        with open('graph.05.dot', 'w') as f: f.write(proj.to_dot())

        proj = CopyInserter(main_memory).visit(proj)
        with open('graph.06.dot', 'w') as f: f.write(proj.to_dot())

        proj = DoFusion(fusion_directives).visit(proj)
        with open('graph.07.dot', 'w') as f: f.write(proj.to_dot())

        proj = AllocateIntermediates(dtype, length).visit(proj)
        with open('graph.08.dot', 'w') as f: f.write(proj.to_dot())

        py_op = proj.find(FunctionDecl, name="py_op")
        schedules = FindParallelism().visit(py_op)
        py_op.defn = parallelize_tasks(schedules)
        with open('graph.09.dot', 'w') as f: f.write(proj.to_dot())

        proj = KernelOutliner(length).visit(proj)
        with open('graph.10.dot', 'w') as f: f.write(proj.to_dot())

        proj = LowerKernelCalls().visit(proj)
        with open('graph.11.dot', 'w') as f: f.write(proj.to_dot())

        proj = RefConverter().visit(proj)
        with open('graph.12.dot', 'w') as f: f.write(proj.to_dot())

        proj = LowerLoopsAndCopies(length).visit(proj)
        with open('graph.13.dot', 'w') as f: f.write(proj.to_dot())

        zipper = ArgZipper()
        proj = zipper.visit( Lifter().visit(proj) )
        c_func.extra_args = zipper.extra_args
        c_func.answer = zipper.answer
        with open('graph.14.dot', 'w') as f: f.write(proj.to_dot())

        print "PARAMS", [(p.name, p.type) for p in proj.find(FunctionDecl).params]
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
