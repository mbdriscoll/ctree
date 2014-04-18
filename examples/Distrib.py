"""
Code generator for the expression A*(B+C), where A, B, and C are vectors
and all operations are element-wise.
"""

n = 0

import logging

logging.basicConfig(level=20)

import numpy as np
import pycl as cl

from ctree.frontend import get_ast
from ctree.c.nodes import *
from ctree.c.types import *
from ctree.templates.nodes import *
from ctree.transformations import *
from ctree.jit import LazySpecializedFunction
from ctree.jit import ConcreteSpecializedFunction

# ---------------------------------------------------------------------------
# Specializer code - nodes

class Vector(CtreeNode):
    def __init__(self, name, loc=None, type=None):
        self.name = name
        self.loc = loc
        self.type = type
        self._loc_cache = {}

    def label(self):
        return "name: %s\\nloc: %s" % (self.name, self.loc)

    def get_type(self):
        return self.type

    def codegen(self):
        return "%s %s" % (self.get_type(), self.name)

    def on(self, mem):
        if mem not in self._loc_cache:
            self._loc_cache[mem] = CopiedVector(self, to=mem)
        return self._loc_cache[mem]

class CopiedVector(Vector):
    _fields = ["data"]
    _next_id = 0
    def __init__(self, data, to=None, name=None):
        self.data = data
        if not name:
            name = "copied%d" % self._next_id
            CopiedVector._next_id += 1
        super(CopiedVector, self).__init__(name=name, loc=to)

    def label(self):
        to = "to: %s" % self.loc
        frm = "from: %s" % self.data.loc
        return "name: %s\\n%s\\n%s" % (self.name, to, frm)


class ComputedVector(Vector):
    _fields = ["data"]
    _next_id = 0
    def __init__(self, data=None, name=None, loc=None):
        self.data = data
        if not name:
            name = "computed%d" % self._next_id
            ComputedVector._next_id += 1
        super(ComputedVector, self).__init__(name=name, loc=data.loc)

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
    def __init__(self):
        self._cache = {}

    def visit_SymbolRef(self, node):
        if node.name not in self._cache:
            self._cache[node.name] = Vector(node.name)
        return self._cache[node.name]

class InsertIntermediates(NodeTransformer):
    def visit_BinaryOp(self, node):
        tree = self.generic_visit(node)
        return ComputedVector(tree, loc=tree.loc)

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


class LocationTagger(NodeTransformer):
    def __init__(self, main_memory, directives):
        self.main_memory = main_memory
        self.directives = iter(directives)

    def visit_BinaryOp(self, node):
        node.loc = self.directives.next()
        return self.generic_visit(node)

    def visit_Vector(self, node):
        node.loc = self.main_memory
        return self.generic_visit(node)


class CopyInserter(NodeTransformer):
    def __init__(self, main_memory):
        self._main_mem = main_memory

    def visit_BinaryOp(self, node):
        node = self.generic_visit(node)
        if node.loc != node.left.loc:
            if not isinstance(node.left, Vector):
                node.left = ComputedVector(node.left)
            node.left = node.left.on(node.loc)
        if node.loc != node.right.loc:
            if not isinstance(node.right, Vector):
                node.right= ComputedVector(node.right)
            node.right = node.right.on(node.loc)
        return node

    def visit_ComputedVector(self, node):
        node.data = self.visit(node.data)
        if node.loc != node.data.loc:
            node.data = node.data.on(node.loc)
        return node

    def visit_CopiedVector(self, node):
        node.data = self.visit(node.data)
        if not isinstance(node.data, ComputedVector):
            node.data = ComputedVector(node.data)
        return node

    def visit_Return(self, node):
        value = self.visit(node.value)
        if value.loc != self._main_mem:
            if not isinstance(node.value, Vector):
                value = ComputedVector(node.value)
            return value.on(self._main_mem)
        elif isinstance(value, BinaryOp):
            return ComputedVector(value, loc=self._main_mem)
        return value

class RemoveRedundantVectors(NodeTransformer):
    def visit_ComputedVector(self, node):
        node.data = self.visit(node.data)
        if isinstance(node.data, Vector) and node.loc == node.data.loc:
            return node.data
        else:
            return node

class AllocateIntermediates(NodeTransformer):
    def __init__(self, dtype, length):
        self.dtype = dtype
        self.length = length
        self.allocated = []

    def visit_ComputedVector(self, node):
        node.mem = node.loc.allocate(self.length, self.dtype)
        self.allocated.append(node)
        return self.generic_visit(node)

    def visit_CopiedVector(self, node):
        node.mem = node.loc.allocate(self.length, self.dtype)
        self.allocated.append(node)
        return self.generic_visit(node)

class Linearize(NodeTransformer):
    def __init__(self):
        self._stmts = []

    def visit_ComputedVector(self, node):
        node = self.generic_visit(node)
        self._stmts.append(node)
        return SymbolRef(node.name)

    def visit_Vector(self, node):
        return SymbolRef(node.name)

class Loopize(NodeTransformer):
    def __init__(self, nElems):
        self.nElems = nElems

    def visit_ComputedVector(self, node):
        i = SymbolRef("i", Int())
        return For(Assign(i, Constant(0)), Lt(i.copy(), Constant(self.nElems)), PostInc(i.copy()), [
            Assign( ArrayRef(SymbolRef(node.name), i.copy()),
                    self.visit(node.data) )
        ])

    def visit_SymbolRef(self, node):
        return ArrayRef(node, SymbolRef("i"))

class Memory(object):
    pass

class MainMemory(Memory):
    def allocate(self, length, dtype):
        return np.empty([length], dtype=dtype)

    def __str__(self):
        return "MainMemory"

class OclMemory(Memory):
    def __init__(self, context):
        self.context = context

    def allocate(self, length, dtype):
        return cl.clCreateBuffer(self.context, length * dtype.itemsize)

    def __str__(self):
        return "OclMemory<%s>" % [dev.name for dev in self.context.devices][0]

# label binary ops with location
BinaryOp.label = lambda self: "op: %s\\nloc: %s" % (self.op, getattr(self, 'loc', '?'))

# ---------------------------------------------------------------------------
# Specializer code - translator

class OpTranslator(LazySpecializedFunction):
    def get_tuning_driver(self):
        from ctree.tune import BruteForceTuningDriver
        from ctree.tune import MinimizeTime
        from ctree.tune import IntegerParameter
        from ctree.tune import BooleanArrayParameter
        from ctree.tune import EnumArrayParameter

        nMuls = 2
        nAdds = 1
        nBinops = nMuls + nAdds
        params = [
            BooleanArrayParameter("distribute", count=nMuls*4),
            EnumArrayParameter("locs", count=nBinops, values=['main']),
            BooleanArrayParameter("fusion", count=nBinops),
        ]

        return BruteForceTuningDriver(params, MinimizeTime())

    def args_to_subconfig(self, args):
        """
        Analyze arguments and return a 'subconfig', a hashable object
        that classifies them. Arguments with identical subconfigs
        might be processed by the same generated code.
        """
        ptrs = tuple(NdPointer.to(a) for a in args)
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
        context = cl.clCreateContextFromType()
        mem_map = {
            'main': MainMemory(),
            'ocl<1>': OclMemory(context),
        }
        main_memory = mem_map['main']

        # run basic conversions
        proj = PyBasicConversions().visit(py_ast)
        fn = proj.find(FunctionDecl, name="py_op")
        fn.return_type = Void()

        # run platform-independent transformations
        distribute_directives = tuner_config['distribute']
        proj = ApplyDistributiveProperty(distribute_directives).visit(proj)

        # identify vectors
        fn.defn = [VectorFinder().visit(fn.defn[0])]

        # set parameter types
        ptrs = arg_config['ptrs']
        for ty, param in zip(ptrs, fn.params):
            param.type = ty

        locs = [mem_map[loc] for loc in tuner_config['locs']]
        fusion_directives = tuner_config['fusion']

        proj = LocationTagger(main_memory, locs).visit(proj)
        proj = InsertIntermediates().visit(proj)
        proj = CopyInserter(main_memory).visit(proj)
        proj = DoFusion(fusion_directives).visit(proj)
        proj = RemoveRedundantVectors().visit(proj)

        assert isinstance(fn.defn[0], Vector)
        # final result: fn.defn[0].name = ans.name

        dtype, length = ptrs[0].ptr._dtype_, arg_config['len']
        allocator = AllocateIntermediates(dtype, length)
        proj = allocator.visit(proj)
        allocator.allocated[0].name = "ans"

        for a in allocator.allocated:
            if isinstance(a.mem, np.ndarray):
                ty = NdPointer.to(a.mem)
            elif isinstance(a.mem, cl.cl_mem):
                raise NotImplementedError("Can't handle cl_mem types.")
            fn.params.append(SymbolRef(a.name, ty))

        linearizer = Linearize()
        proj = linearizer.visit(proj)
        fn.defn = linearizer._stmts

        loopizer = Loopize(length)
        fn.defn = [loopizer.visit(stmt) for stmt in fn.defn]

        c_func = ElementwiseFunction()
        c_func.intermediates = [a.mem for a in allocator.allocated]

        global n
        with open('graph.%d.dot' % n, 'w') as f:
            f.write(proj.to_dot())
        n += 1

        return c_func.finalize("py_op", proj, fn.get_type().as_ctype())

class ElementwiseFunction(ConcreteSpecializedFunction):
    def __init__(self):
        self.context = cl.clCreateContextFromType()
        self.queue = cl.clCreateCommandQueue(self.context)

    def finalize(self, entry_name, proj, typesig):
        self._c_function = self._compile(entry_name, proj, typesig)
        return self

    def __call__(self, *args):
        full_args = list(args) + self.intermediates
        self._c_function(*full_args)
        return np.copy(self.intermediates[0])


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
    for i in range(16):
      a = np.arange(n, dtype=np.float32())
      b = np.ones(n, dtype=np.float32())
      c = np.ones(n, dtype=np.float32())

      actual = c_op(a, b, c)
      expected = py_op(a, b, c)

      np.testing.assert_array_equal(actual, expected)

    print("Success.")


if __name__ == '__main__':
    main()
