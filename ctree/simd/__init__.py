from ctree.simd.types import m256d

from ctree.types import register_type_codegenerators

register_type_codegenerators({
    m256d: lambda t: "__m256d"
})
