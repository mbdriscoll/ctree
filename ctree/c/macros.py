"""
Macros for simplifying construction of C programs.
"""

from ctree.c.nodes import SymbolRef, CtreeNode, FunctionCall, String


def NULL():
    """
    The NULL symbol.
    """
    return SymbolRef("NULL")


def printf(fmt, *args):
    """
    Makes a printf call. Args must be CtreeNodes.
    """
    for arg in args:
        assert isinstance(arg, CtreeNode)
    return FunctionCall(SymbolRef("printf"),
                        [String(fmt)] + list(args))
