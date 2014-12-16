"""
OpenCL nodes supported by ctree.
"""

from ctree.nodes import *


class OclNode(CtreeNode):
    """Base class for all OpenCL nodes supported by ctree."""

    def codegen(self, indent=0):
        """generate ocl code for this node"""
        from ctree.ocl.codegen import OclCodeGen

        return OclCodeGen(indent).visit(self)

    def label(self, indent=0):
        """generate dot element for this node"""
        from ctree.ocl.dotgen import OclDotLabeller

        return OclDotLabeller().visit(self)


class OclFile(OclNode, File):
    """Represents a .cl file."""
    _ext = "cl"

    def __init__(self, name="generated", body=None, path = None):
        if not body:
            body = []
        #TODO: Inspect complains about 2 args to __init__
        super(OclFile, self).__init__(name, body, path)

    def _compile(self, program_text):
        """
        write the ocl program to a text file and compile it
        """
        import os
        cl_src_file = os.path.join(self.path, self.get_filename())
        if not os.path.exists(cl_src_file):
            log.info("file for generated OpenCL: %s" % cl_src_file)
            log.info("generated OpenCL code: (((\n%s\n)))" % program_text)

            # write program text to C file
            with open(cl_src_file, 'w') as cl_file:
                cl_file.write(program_text)
        else:
            log.info("OpenCL file already generated")
        import llvm.core
        return llvm.core.Module.new("empty cl module")
