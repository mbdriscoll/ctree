"""
Code generation for C preprocessing directives.
"""

from ctree.codegen import CodeGenVisitor


class CppCodeGen(CodeGenVisitor):
    """
    Visitor to generate C preprocessor directives.
    """

    def visit_CppInclude(self, node):
        if node.angled_brackets:
            return "#include <%s>" % node.target
        else:
            return '#include "%s"' % node.target

    def visit_CppComment(self, node):
        return "// " + ("\n" + self._tab() + "// ").join(node.text.splitlines())

    def visit_CppDefine(self, node):
        params = ", ".join(map(str, node.params))
        return "#define %s(%s) (%s)" % (node.name, params, node.body)
