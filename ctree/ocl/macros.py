"""
Macros for simplifying construction of OpenCL
programs.
"""

from ctree.c.nodes import SymbolRef, Block, Assign, FunctionCall
from ctree.c.nodes import If, Eq, NotEq, Or, Not, Ref, Constant, String
from ctree.c.types import Ptr, Long, FILE
from ctree.c.macros import NULL, printf
from ctree.c.types import Int


def CL_DEVICE_TYPE_GPU():
    return SymbolRef("CL_DEVICE_TYPE_GPU")


def CL_DEVICE_TYPE_CPU():
    return SymbolRef("CL_DEVICE_TYPE_CPU")


def CL_DEVICE_TYPE_ACCELERATOR():
    return SymbolRef("CL_DEVICE_TYPE_ACCELERATOR")


def CL_DEVICE_TYPE_DEFAULT():
    return SymbolRef("CL_DEVICE_TYPE_DEFAULT")


def CL_DEVICE_TYPE_ALL():
    return SymbolRef("CL_DEVICE_TYPE_ALL")


def CL_SUCCESS():
    return SymbolRef("CL_SUCCESS")
