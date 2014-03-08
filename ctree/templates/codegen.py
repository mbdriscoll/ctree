"""
Code generation for template nodes.
"""

from ctree.codegen import CodeGenVisitor


class TemplateCodeGen(CodeGenVisitor):
    """
    Visitor to generate templated code.
    """
    def visit_TemplateNode(self, node):
        """Convert this template to a string."""
        resolved_children = {key: child.codegen() for key, child in node._children.items()}
        resolved_txt = node._template.safe_substitute(resolved_children)
        indented_text = ("\n" + self._tab()).join(resolved_txt.splitlines())
        return indented_text

    def visit_StringTemplate(self, node):
        """Convert this StringTemplate to a string."""
        return self.visit_TemplateNode(node)

    def visit_FileTemplate(self, node):
        """Convert this FileTemplate to a string."""
        return self.visit_TemplateNode(node)
