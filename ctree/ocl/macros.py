"""
Macros for simplifying construction of OpenCL
programs.
"""

import ast
from ctypes import c_size_t

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

def CLK_GLOBAL_MEM_FENCE():
    return SymbolRef("CLK_GLOBAL_MEM_FENCE")


def barrier(arg):
    return FunctionCall(SymbolRef('barrier'), [arg])


def get_local_id(id):
    return FunctionCall(SymbolRef('get_local_id'), [Constant(id)])


def get_global_id(id):
    return FunctionCall(SymbolRef('get_global_id'), [Constant(id)])


def get_group_id(id):
    return FunctionCall(SymbolRef('get_group_id'), [Constant(id)])


def get_local_size(id):
    return FunctionCall(SymbolRef('get_local_size'), [Constant(id)])


def get_global_size(id):
    return FunctionCall(SymbolRef('get_global_size'), [Constant(id)])


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

def clEnqueueCopyBuffer(queue, src_buf, dst_buf, src_offset=0, dst_offset=0, cb=0):
    if isinstance(src_buf, str):      src_buf = SymbolRef(src_buf)
    if isinstance(dst_buf, str):      dst_buf = SymbolRef(dst_buf)
    if isinstance(src_offset, int):   src_offset = Constant(src_offset)
    if isinstance(dst_offset, int):   dst_offset = Constant(dst_offset)
    if isinstance(cb, int):           cb = Constant(cb)

    num_events = Constant(0)
    event_list_ptr = NULL()
    evt = NULL()

    return FunctionCall(SymbolRef('clEnqueueCopyBuffer'), [
        queue, src_buf, dst_buf, src_offset, dst_offset, cb, num_events, event_list_ptr, evt])

def clSetKernelArg(kernel, arg_index, arg_size, arg_value):
    if isinstance(kernel, str): kernel = SymbolRef(kernel)
    if isinstance(arg_index, int): arg_index = Constant(arg_index)
    if isinstance(arg_size, int): arg_size = Constant(arg_size)
    if isinstance(arg_value, str): arg_value = Ref(SymbolRef(arg_value))
    return FunctionCall(SymbolRef("clSetKernelArg"),
        [kernel, arg_index, arg_size, arg_value])

def clEnqueueNDRangeKernel(queue, kernel, work_dim=1, work_offset=0, global_size=0, local_size=0):
    assert isinstance(queue, SymbolRef)
    assert isinstance(kernel, SymbolRef)
    global_size_sym = SymbolRef('global_size', c_size_t())
    local_size_sym = SymbolRef('local_size', c_size_t())
    call = FunctionCall(SymbolRef("clEnqueueNDRangeKernel"), [
        queue, kernel,
        work_dim, work_offset,
        Ref(global_size_sym.copy()), Ref(local_size_sym.copy()),
        0, NULL(), NULL()
    ])

    return Block([
        Assign(global_size_sym, Constant(global_size)),
        Assign(local_size_sym, Constant(local_size)),
        call
    ])
