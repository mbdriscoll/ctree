"""
Macros for simplifying construction of OpenCL
programs.
"""

from ctree.c.nodes import *
from ctree.c.types import *
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

def safe_clGetDeviceIDs(platform=NULL(), device_type=CL_DEVICE_TYPE_DEFAULT(),
                        num_entries=1, device_id=NULL(),
                        num_devices=NULL(), on_failure=[]):
  # int to track exit status
  err = SymbolRef.unique("err", Int())

  # put failure code in list to go under If.elze
  if not isinstance(on_failure, list):
    on_failure = [on_failure]

  return Block([
    Assign(err.copy(declare=True),
      FunctionCall(SymbolRef("clGetDeviceIDs"), [
        platform, device_type, num_entries, device_id, num_devices])),
    If(NotEq(err.copy(), CL_SUCCESS()), [
      printf(r"Error: Failed to create a device group!\n"),
    ] + on_failure),
  ])

def safe_clCreateContext(context, properties=NULL(), num_devices=1,
      devices=NULL(), pfn_notify=NULL(), user_data=NULL(), on_failure=[]):

  # int to track exit status
  err = SymbolRef.unique("err", Int())

  # put failure code in list to go under If.elze
  if not isinstance(on_failure, list):
    on_failure = [on_failure]

  tree = Block([
    err.copy(declare=True),
    Assign(context.copy(),
      FunctionCall(SymbolRef("clCreateContext"), [
        properties, num_devices, devices, pfn_notify,
        user_data, Ref(err.copy()),
      ])
    ),
    If(Or(Not(context.copy()), NotEq(err.copy(), Constant(0))), [
      printf(r"Error: Failed to create a compute context!\n"),
    ], []),
  ])

  return tree


def safe_clCreateCommandQueue(commands, context, device_id, properties=Constant(0), on_failure=[]):
  # int to track exit status
  err = SymbolRef.unique("err", Int())

  # put failure code in list to go under If.elze
  if not isinstance(on_failure, list):
    on_failure = [on_failure]

  tree = Block([
    err.copy(declare=True),
    Assign(commands.copy(),
      FunctionCall(SymbolRef("clCreateCommandQueue"), [
        context, device_id, properties, Ref(err.copy()),
      ])
    ),
    If(Or(Not(commands.copy()), NotEq(err.copy(), Constant(0))), [
      printf(r"Error: Failed to create a command commands!\n"),
    ], []),
  ])

  return tree

def read_program_into_string(kernel_source, kernel_path):
  kernel_file = SymbolRef("kernel_file", Ptr(FILE()))
  kernel_size = SymbolRef("kernel_size", Long())
  tree = Block([
    Assign(kernel_file.copy(declare=True),
           FunctionCall(SymbolRef("fopen"), [kernel_path.copy(), String("rb")])),
    If(Eq(kernel_file.copy(), NULL()), [
      printf(r"Error: couldn't open kernel file.\n"),
    ], []),
    FunctionCall(SymbolRef("fseek"), [kernel_file.copy(), Constant(0), SymbolRef("SEEK_END")]),
    Assign(kernel_size.copy(declare=True), FunctionCall(SymbolRef("ftell"), [kernel_file.copy()])),
    FunctionCall(SymbolRef("rewind"), [kernel_file.copy()]),
    Assign(kernel_source.copy(), FunctionCall(SymbolRef("malloc"), [Mul(kernel_size.copy(), SizeOf(Char()))])),

  ])
  return tree

"""
128     FILE *kernelFile = fopen("/Users/mbdriscoll/tmp/learn_ocl/square.cl", "rb");
129     if (kernelFile == NULL) {
130         printf("Error: Coudn't open kernel file.\n");
131         return EXIT_FAILURE;
132     }
134     fseek(kernelFile, 0 , SEEK_END);
135     long kernelFileSize = ftell(kernelFile);
136     rewind(kernelFile);
140     char *KernelSource = malloc(kernelFileSize*sizeof(char));
141     if (KernelSource == NULL) {
142         printf("Error: failed to allocate memory to hold kernel text.\n");
143         return EXIT_FAILURE;
144     }
148     int result = fread(KernelSource, sizeof(char), kernelFileSize, kernelFile);
149     if (result != kernelFileSize) {
150         printf("Error: read fewer bytes of kernel text than expected.\n");
151         return EXIT_FAILURE;
153     fclose(kernelFile);
"""
