"""
OpenCL nodes supported by ctree.
"""

from ctree.node import *


class OclNode(CtreeNode):
    """Base class for all OpenCL nodes supported by ctree."""

    def codegen(self, indent=0):
        from ctree.ocl.codegen import OclCodeGen

        return OclCodeGen(indent).visit(self)

    def dotgen(self, indent=0):
        from ctree.ocl.dotgen import OclDotGen

        return OclDotGen().visit(self)


class OclFile(OclNode, File):
    """Represents a .cl file."""

    def __init__(self, name="generated", body=[]):
        #TODO: Inspect complains about 2 args to __init__
        super(OclFile, self).__init__(name, body)
        self._ext = "cl"

    def _compile(self, program_text, compilation_dir):
        cl_src_file = os.path.join(compilation_dir, self.get_filename())
        log.info("File for generated OpenCL: %s" % cl_src_file)
        log.info("Generated OpenCL code: <<<\n%s\n>>>" % program_text)

        # write program text to C file
        with open(cl_src_file, 'w') as cl_file:
            cl_file.write(program_text)

        import llvm.core

        return llvm.core.Module.new("empty cl module")
