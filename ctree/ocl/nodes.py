"""
OpenCL nodes supported by ctree.
"""

from ctree.nodes import *
import hashlib


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
        #TODO: Inspect complains about 2 args to __init__
        super(OclFile, self).__init__(name, body, path)

    def _compile(self, program_text):
        """
        write the ocl program to a text file and compile it
        """
        import os
        new_hash = hashlib.sha512(program_text.strip().encode()).hexdigest()
        recreate_source = program_text != self._empty and new_hash != self.program_hash
        self.program_hash = new_hash
        cl_src_file = os.path.join(self.path, self.get_filename())
        if recreate_source:
            log.info('Recreating source')
            log.info("file for generated OpenCL: %s" % cl_src_file)
            log.info("generated OpenCL code: (((\n%s\n)))" % program_text)

            # write program text to CL file
            with open(cl_src_file, 'w') as cl_file:
                cl_file.write(program_text)
        else:
            log.info("OpenCL file already generated")
        return None

    def codegen(self, indent=0):
        if self.body:
            return super(OclFile, self).codegen(indent)
        with open(os.path.join(self.path, self.get_filename())) as cl_file:
            return cl_file.read()
