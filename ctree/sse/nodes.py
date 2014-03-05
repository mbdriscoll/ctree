"""
SSE vector nodes supported by ctree.
"""

from ctree.nodes import CtreeNode


class SSENode(CtreeNode):
    """Base class for all SSE nodes supported by ctree."""

    def codegen(self, indent=0):
        from ctree.sse.codegen import SseCodeGen

        return SseCodeGen(indent).visit(self)

    def dotgen(self, indent=0):
        from ctree.sse.dotgen import SseDotGen

        return SseDotGen().visit(self)
