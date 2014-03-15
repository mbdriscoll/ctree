"""
Macros for working with SIMD vector types.
"""

from ctree.c.nodes import FunctionCall, SymbolRef

def _make_call(name, nArgs):
    def _the_call(*args):
        assert len(args) == nArgs, \
            "Macro expected %d args, got %d." % (nArgs, len(args))
        return FunctionCall(SymbolRef(name), args)
    return _the_call

mm256_storeu_pd = _make_call("_mm256_storeu_pd", 2)
mm256_loadu_pd  = _make_call("_mm256_loadu_pd", 1)
mm256_load_pd   = _make_call("_mm256_load_pd", 1)
mm256_set1_pd   = _make_call("_mm256_set1_pd", 1)
mm256_add_pd    = _make_call("_mm256_add_pd", 2)
mm256_mul_pd    = _make_call("_mm256_mul_pd", 2)
