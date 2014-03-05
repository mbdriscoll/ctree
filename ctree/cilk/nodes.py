"""
Cilk nodes supported by ctree.
"""

from ctree.node import CtreeNode


class CilkNode(CtreeNode):
    """Base class for all Cilk nodes supported by ctree."""

    def codegen(self, indent=0):
        from ctree.cilk.codegen import CilkCodeGen

        return CilkCodeGen(indent).visit(self)

    def dotgen(self, indent=0):
        from ctree.cilk.dotgen import CilkDotGen

        return CilkDotGen().visit(self)
