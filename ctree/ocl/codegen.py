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
