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

def CLK_LOCAL_MEM_FENCE():
    return SymbolRef("CLK_LOCAL_MEM_FENCE")

def barrier(arg):
    return FunctionCall(SymbolRef('barrier'), [arg])

def get_local_id(id):
    return FunctionCall(SymbolRef('get_local_id'), [Constant(id)])

def get_global_id(id):
    return FunctionCall(SymbolRef('get_global_id'), [Constant(id)])

def get_local_size(id):
    return FunctionCall(SymbolRef('get_local_size'), [Constant(id)])

def get_num_groups(id):
    return FunctionCall(SymbolRef('get_num_groups'), [Constant(id)])

def clReleaseMemObject(arg):
    return FunctionCall(SymbolRef('clReleaseMemObject'), [arg])
