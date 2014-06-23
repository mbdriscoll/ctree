from ctree.types import CtreeType


class SimdType(CtreeType):
    """Base class for all SIMD Types."""

    def codegen(self, indent=0):
        from ctree.simd.codegen import SimdCodeGen

        return SimdCodeGen().visit(self)


class m256d(SimdType):
    pass
