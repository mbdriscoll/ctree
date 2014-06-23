"""
SIMD vector nodes supported by ctree.
"""

from ctree.nodes import CtreeNode


class SimdNode(CtreeNode):
    """Base class for all SIMD nodes supported by ctree."""

    def codegen(self, indent=0):
        from ctree.sse.codegen import SimdCodeGen

        return SimdCodeGen(indent).visit(self)

    def label(self):
        from ctree.sse.dotgen import SimdDotLabeller

        return SimdDotLabeller().visit(self)
