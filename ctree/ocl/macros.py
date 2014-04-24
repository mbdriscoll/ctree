"""
Macros for simplifying construction of OpenCL
programs.
"""

import ast

from ctree.c.nodes import SymbolRef, Block, Assign, FunctionCall
from ctree.c.nodes import If, Eq, NotEq, Or, Not, Ref, Constant, String
from ctree.c.macros import NULL, printf


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

def clEnqueueWriteBuffer(queue, buf, blocking, offset, cb, ptr, num_events=0, evt_list_ptr=None, evt=None):
    if     isinstance(buf, str):              buf = SymbolRef(buf)
    if     isinstance(blocking, bool):        blocking = Constant(int(blocking))
    if     isinstance(ptr, str):              ptr = SymbolRef(ptr)
    if not isinstance(offset, ast.AST):       offset = Constant(offset)
    if not isinstance(cb, ast.AST):           cb = Constant(cb)
    if not isinstance(num_events, ast.AST):   num_events = Constant(num_events)
    if not isinstance(evt_list_ptr, ast.AST): event_list_ptr = NULL()
    if not isinstance(evt, ast.AST):          evt = NULL()
    return FunctionCall(SymbolRef('clEnqueueWriteBuffer'), [
        queue, buf, blocking, offset, cb, ptr, num_events, event_list_ptr, evt])

def clEnqueueReadBuffer(queue, buf, blocking, offset, cb, ptr, num_events=0, evt_list_ptr=None, evt=None):
    if     isinstance(buf, str):              buf = SymbolRef(buf)
    if     isinstance(blocking, bool):        blocking = Constant(int(blocking))
    if     isinstance(ptr, str):              ptr = SymbolRef(ptr)
    if not isinstance(offset, ast.AST):       offset = Constant(offset)
    if not isinstance(cb, ast.AST):           cb = Constant(cb)
    if not isinstance(num_events, ast.AST):   num_events = Constant(num_events)
    if not isinstance(evt_list_ptr, ast.AST): event_list_ptr = NULL()
    if not isinstance(evt, ast.AST):          evt = NULL()
    return FunctionCall(SymbolRef('clEnqueueReadBuffer'), [
        queue, buf, blocking, offset, cb, ptr, num_events, event_list_ptr, evt])
