import ctypes

from ctree.types import CtreeType, CtreeTypeResolver, TypeFetcher, get_ctree_type


class OclType(CtreeType):
    """Base class for all built-in OpenCL Types."""
    def __init__(self, ctype=None):
        self.ctype = ctype

    def codegen(self, indent=0):
        from ctree.ocl.codegen import OclCodeGen

        return OclCodeGen().visit(self)

    def as_ctype(self):
        return self.ctype


class cl_device_id(OclType):
    pass


class cl_context(OclType):
    pass


class cl_command_queue(OclType):
    pass


class cl_program(OclType):
    pass


class cl_kernel(OclType):
    pass


class cl_buffer(OclType):
    @staticmethod
    def to(ocl_buf):
        return OclType(ocl_buf)
