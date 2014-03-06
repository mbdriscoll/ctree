"""
C preprocessor nodes supported by ctree.
"""

from ctree.nodes import CtreeNode


class CppNode(CtreeNode):
    """Base class for all C Preprocessor nodes in ctree."""

    def codegen(self, indent=0):
        from ctree.cpp.codegen import CppCodeGen

        return CppCodeGen(indent).visit(self)

    def _to_dot(self):
        from ctree.cpp.dotgen import CppDotGen

        return CppDotGen().visit(self)

    def _requires_semicolon(self):
        return False


class CppInclude(CppNode):
    """Represents #include <foo.h>."""

    def __init__(self, target="", angled_brackets=True):
        self.target = target
        self.angled_brackets = angled_brackets
