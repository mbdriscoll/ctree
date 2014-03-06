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


def safe_clGetDeviceIDs(platform=NULL(), device_type=CL_DEVICE_TYPE_DEFAULT(),
                        num_entries=Constant(1), device_id=NULL(),
                        num_devices=NULL(), on_failure=None):
    # int to track exit status
    err = SymbolRef.unique("err", Int())

    # put failure code in list to go under If.elze
    if on_failure:
        if not isinstance(on_failure, list):
            on_failure = [on_failure]
    else:
        on_failure = []

    return Block([
        Assign(err.copy(declare=True),
               FunctionCall(SymbolRef("clGetDeviceIDs"), [
                   platform, device_type, num_entries, device_id, num_devices])),
        If(NotEq(err.copy(), CL_SUCCESS()), [
                                                printf(r"Error: Failed to create a device group!\n"),
        ] + on_failure),
    ])


def safe_clCreateContext(context, properties=NULL(), num_devices=Constant(1),
                         devices=NULL(), pfn_notify=NULL(), user_data=NULL(), on_failure=None):
    # int to track exit status
    err = SymbolRef.unique("err", Int())

    # put failure code in list to go under If.elze
    if on_failure:
        if not isinstance(on_failure, list):
            on_failure = [on_failure]
    else:
        on_failure = []

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


def safe_clCreateCommandQueue(commands, context, device_id, properties=Constant(0), on_failure=None):
    # int to track exit status
    err = SymbolRef.unique("err", Int())

    # put failure code in list to go under If.elze
    if on_failure:
        if not isinstance(on_failure, list):
            on_failure = [on_failure]
    else:
        on_failure = []

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
        Assign(kernel_source.copy(), FunctionCall(SymbolRef("malloc"), [kernel_size.copy()])),

    ])
    return tree


def read_program_into_string(symbol_node, path_node):
    """
    Builts a block that opens the given file, reads it into memory,
    and assigns symbol_node to point to it.
    """

    template = """
        FILE *kernelFile = fopen("/Users/mbdriscoll/tmp/learn_ocl/square.cl", "rb");
        if (kernelFile == NULL) {
            printf("Error: Coudn't open kernel file.\n");
            return EXIT_FAILURE;
        }
        fseek(kernelFile, 0 , SEEK_END);
        long kernelFileSize = ftell(kernelFile);
        rewind(kernelFile);
        char *KernelSource = malloc(kernelFileSize*sizeof(char));
        if (KernelSource == NULL) {
            printf("Error: failed to allocate memory to hold kernel text.\n");
            return EXIT_FAILURE;
        }
        int result = fread(KernelSource, sizeof(char), kernelFileSize, kernelFile);
        if (result != kernelFileSize) {
            printf("Error: read fewer bytes of kernel text than expected.\n");
            return EXIT_FAILURE;
        fclose(kernelFile);
    """

