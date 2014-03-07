"""
Parses the python AST below, transforms it to C, JITs it, and runs it.
"""

import logging

logging.basicConfig(level=20)

import numpy as np

from ctree.c.nodes import *
from ctree.c.types import *
from ctree.cpp.nodes import *
from ctree.ocl.nodes import *
from ctree.ocl.types import *
from ctree.ocl.macros import *
from ctree.templates.nodes import StringTemplate
from ctree.transformations import *
from ctree.jit import LazySpecializedFunction
from ctree.types import get_ctree_type
from ctree.dotgen import to_dot

# ---------------------------------------------------------------------------
# Specializer code

template = r"""\
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <OpenCL/opencl.h>

int apply_all($array_decl)
{
    const unsigned int count = $count;  // number of elements in array
    int err;                            // error code returned from api calls

    size_t global;                      // global domain size for our calculation
    size_t local;                       // local domain size for our calculation

    cl_device_id device_id;             // compute device id
    cl_context context;                 // compute context
    cl_command_queue commands;          // compute command queue
    cl_program program;                 // compute program
    cl_kernel kernel;                   // compute kernel

    cl_mem device_data;                       // device memory used for the data array

    // Connect to a compute device
    //
    int gpu = 1;
    err = clGetDeviceIDs(NULL, gpu ? CL_DEVICE_TYPE_GPU : CL_DEVICE_TYPE_CPU, 1, &device_id, NULL);
    if (err != CL_SUCCESS)
    {
        printf("Error: Failed to create a device group!\n");
        return err;
    }

    // Create a compute context
    //
    context = clCreateContext(0, 1, &device_id, NULL, NULL, &err);
    if (!context)
    {
        printf("Error: Failed to create a compute context!\n");
        return err;
    }

    // Create a command commands
    //
    commands = clCreateCommandQueue(context, device_id, 0, &err);
    if (!commands)
    {
        printf("Error: Failed to create a command commands!\n");
        return err;
    }

    // Read the kernel into a string
    //
    FILE *kernelFile = fopen($kernel_path, "rb");
    if (kernelFile == NULL) {
        printf("Error: Coudn't open kernel file.\n");
        return err;
    }

    fseek(kernelFile, 0 , SEEK_END);
    long kernelFileSize = ftell(kernelFile);
    rewind(kernelFile);

    // Allocate memory to hold kernel
    //
    char *KernelSource = malloc(kernelFileSize*sizeof(char));
    if (KernelSource == NULL) {
        printf("Error: failed to allocate memory to hold kernel text.\n");
        return err;
    }

    // Read the kernel into memory
    //
    int result = fread(KernelSource, sizeof(char), kernelFileSize, kernelFile);
    if (result != kernelFileSize) {
        printf("Error: read fewer bytes of kernel text than expected.\n");
        return err;
    }
    fclose(kernelFile);

    // Create the compute program from the source buffer
    //
    program = clCreateProgramWithSource(context, 1, (const char **) & KernelSource, NULL, &err);
    if (!program)
    {
        printf("Error: Failed to create compute program!\n");
        return err;
    }

    // Build the program executable
    //
    err = clBuildProgram(program, 0, NULL, NULL, NULL, NULL);
    if (err != CL_SUCCESS)
    {
        size_t len;
        char buffer[2048];

        printf("Error: Failed to build program executable!\n");
        clGetProgramBuildInfo(program, device_id, CL_PROGRAM_BUILD_LOG, sizeof(buffer), buffer, &len);
        printf("%s\n", buffer);
        return err;
    }

    // Create the compute kernel in the program we wish to run
    //
    kernel = clCreateKernel(program, $kernel_name, &err);
    if (!kernel || err != CL_SUCCESS)
    {
        printf("Error: Failed to create compute kernel!\n");
        return err;
    }

    // Create the data array in device memory for our calculation
    //
    device_data = clCreateBuffer(context, CL_MEM_READ_WRITE, sizeof($array_ref[0]) * count, NULL, NULL);
    if (!device_data)
    {
        printf("Error: Failed to allocate device memory!\n");
        return err;
    }

    // Write our data set into the data array in device memory
    //
    err = clEnqueueWriteBuffer(commands, device_data, CL_TRUE, 0, sizeof($array_ref[0]) * count, $array_ref, 0, NULL, NULL);
    if (err != CL_SUCCESS)
    {
        printf("Error: Failed to write to source array!\n");
        return err;
    }

    // Set the arguments to our compute kernel
    //
    err = 0;
    err  = clSetKernelArg(kernel, 0, sizeof(cl_mem), &device_data);
    if (err != CL_SUCCESS)
    {
        printf("Error: Failed to set kernel arguments! %d\n", err);
        return err;
    }

    // Get the maximum work group size for executing the kernel on the device
    //
    err = clGetKernelWorkGroupInfo(kernel, device_id, CL_KERNEL_WORK_GROUP_SIZE, sizeof(local), &local, NULL);
    if (err != CL_SUCCESS)
    {
        printf("Error: Failed to retrieve kernel work group info! %d\n", err);
        return err;
    }

    // Execute the kernel over the entire range of our 1d input data set
    // using the maximum number of work group items for this device
    //
    global = count;
    err = clEnqueueNDRangeKernel(commands, kernel, 1, NULL, &global, &local, 0, NULL, NULL);
    if (err)
    {
        printf("Error: Failed to execute kernel!\n");
        return err;
    }

    // Wait for the command commands to get serviced before reading back results
    //
    clFinish(commands);

    // Read back the results from the device to verify the output
    //
    err = clEnqueueReadBuffer( commands, device_data, CL_TRUE, 0, sizeof($array_ref[0]) * count, $array_ref, 0, NULL, NULL );
    if (err != CL_SUCCESS)
    {
        printf("Error: Failed to read data array! %d\n", err);
        return err;
    }

    // Shutdown and cleanup
    //
    clReleaseMemObject(device_data);
    clReleaseProgram(program);
    clReleaseKernel(kernel);
    clReleaseCommandQueue(commands);
    clReleaseContext(context);

    return 0;
}
"""

class OpTranslator(LazySpecializedFunction):
    def args_to_subconfig(self, args):
        """
        Analyze arguments and return a 'subconfig', a hashable object
        that classifies them. Arguments with identical subconfigs
        might be processed by the same generated code.
        """
        A = args[0]
        return len(A), A.dtype, A.ndim, A.shape

    def transform(self, py_ast, program_config):
        """
        Convert the Python AST to a C AST according to the directions
        given in program_config.
        """
        len_A, A_dtype, A_ndim, A_shape = program_config[0]
        A_type = NdPointer(A_dtype, A_ndim, A_shape)

        apply_one = PyBasicConversions().visit(py_ast.body[0])
        apply_one_typesig = FuncType(A_type.get_base_type(), [A_type.get_base_type()])
        apply_one.set_typesig(apply_one_typesig)

        apply_kernel = FunctionDecl(Void(), "apply_kernel",
                                    params=[SymbolRef("A", A_type)],
                                    defn=[
                                        Assign(SymbolRef("i", Int()),
                                               FunctionCall(SymbolRef("get_global_id"), [Constant(0)])),
                                        If(Lt(SymbolRef("i"), Constant(len_A)), [
                                            Assign(ArrayRef(SymbolRef("A"), SymbolRef("i")),
                                                   FunctionCall(SymbolRef("apply"),
                                                                [ArrayRef(SymbolRef("A"), SymbolRef("i"))]))
                                        ])
                                    ])

        # add opencl type qualifiers
        apply_kernel.set_kernel()
        apply_kernel.params[0].set_global()

        kernel = OclFile("kernel", [apply_one, apply_kernel])

        template_args = {
            'array_decl': SymbolRef("data", A_type),
            'array_ref':  SymbolRef("data"),
            'count':      Constant(len_A),
            'kernel_path': Cast(Ptr(Char()), kernel.get_generated_path_ref()),
            'kernel_name': String(apply_kernel.name),
        }

        control = CFile("control", [
            StringTemplate(template, template_args),
        ])
        tree = Project([kernel, control])

        with open("graph.dot", 'w') as f:
          f.write( to_dot(tree) )

        entry_point_typesig = FuncType(Int(), [A_type]).as_ctype()
        return tree, entry_point_typesig


class ArrayOp(object):
    """
    A class for managing independent operation on elements
    in numpy arrays.
    """

    def __init__(self):
        """Instantiate translator."""
        from ctree.frontend import get_ast

        self.c_apply_all = OpTranslator(get_ast(self.apply), "apply_all")

    def __call__(self, A):
        """Apply the operator to the arguments via a generated function."""
        retval = self.c_apply_all(A)
        assert retval == 0, "Specialized function exited with non-zero value: %d" % retval


# ---------------------------------------------------------------------------
# User code

class Doubler(ArrayOp):
    """Double elements of the array."""

    def apply(x):
        return x * 2


def py_doubler(A):
    for i in range(len(A)):
        A[i] *= 2


def main():
    c_doubler = Doubler()

    # doubling doubles
    actual_d = np.ones(1024, dtype=np.float32)
    expected_d = np.ones(1024, dtype=np.float32)
    c_doubler(actual_d)
    py_doubler(expected_d)
    np.testing.assert_array_equal(actual_d, expected_d)

    print("Success.")


if __name__ == '__main__':
    main()
