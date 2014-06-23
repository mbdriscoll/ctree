"""
Code generation for OpenCL.
"""

from ctree.codegen import CodeGenVisitor


class OclCodeGen(CodeGenVisitor):
    """
    Visitor to generate OpenCL code.
    """

    def visit_OclFile(self, node):
        stmts = self._genblock(node.body, insert_curly_brackets=False, increase_indent=False)
        return '// <file: %s>%s' % (node.get_filename(), stmts)

    def visit_cl_device_id(self, node):
        return "cl_device_id"

    def visit_cl_context(self, node):
        return "cl_context"

    def visit_cl_command_queue(self, node):
        return "cl_command_queue"

    def visit_cl_program(self, node):
        return "cl_program"

    def visit_cl_kernel(self, node):
        return "cl_kernel"

    def visit_cl_buffer(self, node):
        return "cl_buffer"
