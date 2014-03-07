"""
DOT generation for template nodes.
"""

from ctree.dotgen import DotGenVisitor


class TemplateDotGen(DotGenVisitor):
    """
    Visitor to generator DOT.
    """
    def label_StringTemplate(self, node):
        return "template: <<<\n%s\n>>>" % \
            node._template.template.replace("\n", "\\n").replace('"', r"\"")
