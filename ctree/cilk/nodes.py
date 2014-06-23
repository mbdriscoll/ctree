"""
Cilk nodes supported by ctree.
"""

from ctree.nodes import CtreeNode


class CilkNode(CtreeNode):
    """Base class for all Cilk nodes supported by ctree."""

    def codegen(self, indent=0):
        from ctree.cilk.codegen import CilkCodeGen

        return CilkCodeGen(indent).visit(self)

    def _to_dot(self, _):
        from ctree.cilk.dotgen import CilkDotLabeller

        return CilkDotLabeller().visit(self)
