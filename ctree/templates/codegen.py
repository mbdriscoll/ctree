"""
Code generation for template nodes.
"""

from ctree.codegen import CodeGenVisitor
from ctree.util import flatten


class TemplateCodeGen(CodeGenVisitor):
    """
    Visitor to generate templated code.
    """
    def _resolve(self, value):
        """
        Generated the string for the given child, which might be a
        list of lists (...of lists...) of nodes. For a single node,
        don't append a semicolon, otherwise append semicolons and
        newlines to each statement if they require it.
        """
        children = list(flatten(value))
        if len(children) == 1:
            return children[0].codegen()
        else:
            body = ""
            for child in children:
                semicolon_opt = ";" if child._requires_semicolon() else ""
                body += self._tab() + child.codegen() + semicolon_opt + "\n"
            return body

    def visit_TemplateNode(self, node):
        """Convert this template to a string."""
        resolved_children = {key: self._resolve(value) for key, value in node._children.items()}
        resolved_txt = node._template.safe_substitute(resolved_children)
        indented_text = ("\n" + self._tab()).join(resolved_txt.splitlines())
        return indented_text

    def visit_StringTemplate(self, node):
        """Convert this StringTemplate to a string."""
        return self.visit_TemplateNode(node)

    def visit_FileTemplate(self, node):
        """Convert this FileTemplate to a string."""
        return self.visit_TemplateNode(node)
