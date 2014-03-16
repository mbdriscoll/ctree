"""
Macros for using OpenMP.
"""

from ctree.c.nodes import FunctionCall, SymbolRef
from ctree.cpp.nodes import CppInclude

def omp_get_num_threads():
    return FunctionCall(SymbolRef("omp_get_num_threads"), [])

def omp_get_thread_num():
    return FunctionCall(SymbolRef("omp_get_thread_num"), [])

def IncludeOmpHeader():
    return CppInclude("omp.h")
