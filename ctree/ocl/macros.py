"""
Macros for simplifying construction of OpenCL
programs.
"""

from ctree.c.nodes import *
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

def safe_clGetDeviceIDs(platform=NULL(), device_type=CL_DEVICE_TYPE_DEFAULT(), num_entries=1, device_id=NULL(), num_devices=NULL()):
  err = SymbolRef.unique("err", Int())
  return Block([
    Assign(err.copy(declare=True),
      FunctionCall(SymbolRef("clGetDeviceIDs"), [
        platform, device_type, num_entries, device_id, num_devices])),
    If(NotEq(err.copy(), CL_SUCCESS()), [
      printf(r"Error: Failed to create a device group!\n"),
      Return(),
    ], []),
  ])
