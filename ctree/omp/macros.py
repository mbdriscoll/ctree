"""
Macros for using OpenMP.
"""

from ctree.c.nodes import FunctionCall, SymbolRef, Block
from ctree.cpp.nodes import CppInclude
from ctree.omp.nodes import OmpParallelSections, OmpSection

def omp_get_num_threads():
    return FunctionCall(SymbolRef("omp_get_num_threads"), [])

def omp_get_thread_num():
    return FunctionCall(SymbolRef("omp_get_thread_num"), [])

def omp_get_wtime():
    return FunctionCall(SymbolRef("omp_get_wtime"), [])

def IncludeOmpHeader():
    return CppInclude("omp.h")


def parallelize_tasks(dag):
    """
    Returns an AST that computes the entries in dag in parallel using
    omp sections. Dag must consist of:
    1) tuples, implying elements must be executed sequentially,
    2) frozensets, implying elements can be executed in parallel,
    3) ASTs, the contents themselves.
    """
    if isinstance(dag, tuple):
        sched = []
        for node in dag:
            sched.extend(parallelize_tasks(node))
        return sched
    elif isinstance(dag, frozenset):
        sched = [OmpSection(body=parallelize_tasks(node)) for node in dag]
        return [OmpParallelSections(sections=sched)]
    else:
        return [dag]

