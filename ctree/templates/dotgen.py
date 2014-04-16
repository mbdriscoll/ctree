"""
DOT generation for template nodes.
"""

import os

from ctree.dotgen import DotGenLabeller


class TemplateDotLabeller(DotGenLabeller):
    """
    Visitor to generator DOT.
    """
    def visit_StringTemplate(self, node):
        return "template: <<<\n%s\n>>>" % \
            node._template.template.replace("\n", "\\n").replace('"', r"\"")

    def visit_FileTemplate(self, node):
        return os.path.basename(node._template_path)
