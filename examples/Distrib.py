"""
Code generator for the expression A*(B+C), where A, B, and C are vectors
and all operations are element-wise.
"""

n = 0

import logging

logging.basicConfig(level=20)

import numpy as np

from ctree.frontend import get_ast
from ctree.c.nodes import *
from ctree.c.types import *
from ctree.templates.nodes import *
from ctree.transformations import *
from ctree.jit import LazySpecializedFunction
from ctree.dotgen import DotGenVisitor

# ---------------------------------------------------------------------------
# Specializer code - nodes

class Vector(CtreeNode):
    def __init__(self, name=None, loc='main', type=None):
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
    def __init__(self, data, to='main', name=None):
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

class DistributiveLaw(NodeTransformer):
    def __init__(self, directives):
        super(DistributiveLaw, self).__init__()
        self._directives = iter(directives)

    def visit_BinaryOp(self, node):
        ab = node.left  = self.visit(node.left)
        cd = node.right = self.visit(node.right)
        dist_left  = isinstance(ab, BinaryOp) and isinstance(ab.op, Op.Add)
        dist_right = isinstance(cd, BinaryOp) and isinstance(cd.op, Op.Add)
        if isinstance(node.op, Op.Mul) and \
           (dist_left or dist_right) and \
           self._directives.next() == True:

            if dist_right and dist_left:
                a, b = ab.left, ab.right
                c, d = cd.left, cd.right
                return Add(Add(Mul(a,c), Mul(b,c)), Add(Mul(a,d), Mul(b,d)))
            elif dist_right:
                c, d = cd.left, cd.right
                return Add(Mul(ab, c), Mul(ab, d))
            elif dist_left:
                a, b = ab.left, ab.right
                return Add(Mul(a, cd), Add(b, cd))
            else:
                raise ValueError("Term shouldn't distribute.")
        else:
            return node

class VectorFinder(NodeTransformer):
    def __init__(self):
        self._cache = {}

    def visit_SymbolRef(self, node):
        if node.name not in self._cache:
            self._cache[node.name] = Vector(node.name)
        return self._cache[node.name]

class InsertIntermediates(NodeTransformer):
    def __init__(self, directives):
        self._directives = iter(directives)

    def visit_BinaryOp(self, node):
        tree = self.generic_visit(node)
        return ComputedVector(tree, loc=tree.loc) if self._directives.next() else tree

    def visit_CopiedVector(self, node):
        tree = self.visit(node.data)
        node.data = ComputedVector(tree, loc=tree.loc)
        return node

class LocationTagger(NodeTransformer):
    def __init__(self, directives):
        self.directives = iter(directives)

    def visit_BinaryOp(self, node):
        node.loc = self.directives.next()
        return self.generic_visit(node)

class CopyInserter(NodeTransformer):
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
        if value.loc != 'main':
            if not isinstance(node.value, Vector):
                value = ComputedVector(node.value)
            return value.on('main')
        elif isinstance(value, BinaryOp):
            return ComputedVector(value, loc='main')
        return value

class RemoveRedundantVectors(NodeTransformer):
    def visit_ComputedVector(self, node):
        node.data = self.visit(node.data)
        if isinstance(node.data, Vector) and node.loc == node.data.loc:
            return node.data
        else:
            return node

# label binary ops with location
BinaryOp.label = lambda self: "op: %s\\nloc: %s" % (self.op, getattr(self, 'loc', None))

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
            BooleanArrayParameter("distribute", count=nMuls),
            BooleanArrayParameter("intermediates", count=nBinops),
            EnumArrayParameter("locs", count=nBinops, values=['main', 'ocl[0]']),
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

        # run basic conversions
        proj = PyBasicConversions().visit(py_ast)
        fn = proj.find(FunctionDecl, name="py_op")
        fn.return_type = Void()

        # run platform-independent transformations
        distribute_directives = tuner_config['distribute']
        proj = DistributiveLaw(distribute_directives).visit(proj)

        # insert parameter to hold answer
        ans = SymbolRef("ans", fn.params[0].type)
        fn.params.insert(0, ans)

        # identify vectors
        fn.defn = [VectorFinder().visit(fn.defn[0])]

        # set parameter types
        ptrs = arg_config['ptrs']
        for ty, param in zip(ptrs, fn.params):
            param.type = ty

        # tag operations with platforms
        locs = tuner_config['locs']
        proj = LocationTagger(locs).visit(proj)

        intermediate_directives = tuner_config['intermediates']
        #proj = InsertIntermediates(intermediate_directives).visit(proj)

        proj = CopyInserter().visit(proj)

        proj = RemoveRedundantVectors().visit(proj)

        global n
        with open('graph.%d.dot' % n, 'w') as f:
            f.write(proj.to_dot())
        n += 1

        """
        proj = ReturnsToWrites(ans).visit(proj)

        intermediates = tuner_config['intermediates']
        proj = VectorIdentifier(intermediates).visit(proj)
        proj = RedudantVectorEliminator().visit(proj)
        proj = CopyInserter().visit(proj)


        """
        fn.defn = [SymbolRef("foo", Int())]

        return proj, fn.get_type().as_ctype()


class Elementwise(object):
    """
    A class for managing independent operation on elements
    in numpy arrays.
    """

    def __init__(self, fn):
        """Instantiate translator."""
        self.c_op = OpTranslator(get_ast(fn), "py_op")

    def __call__(self, *args):
        """Apply the operator to the arguments via a generated function."""
        answer = np.zeros_like(args[0])
        self.c_op(answer, *args)
        return answer


# ---------------------------------------------------------------------------
# User code

def py_op(a, b, c):
    #return (a + b) * (c + d)
    return a * (b + c)

def main():
    n = 12
    c_op = Elementwise(py_op)

    # doubling doubles
    for i in range(16):
      a = np.arange(n, dtype=np.float32)
      b = np.ones(n, dtype=np.float32)
      c = np.ones(n, dtype=np.float32)

      actual = c_op(a, b, c)
      expected = py_op(a, b, c)

      #np.testing.assert_array_equal(actual, expected)

    print("Success.")


if __name__ == '__main__':
    main()
