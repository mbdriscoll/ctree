from ctree.nodes import CtreeNode

class TemplateNode(CtreeNode):
    """Base class for all template nodes."""
    def codegen(self, indent=0):
        from ctree.templates.codegen import TemplateCodeGen

        return TemplateCodeGen(indent).visit(self)

    def _to_dot(self):
        from ctree.templates.dotgen import TemplateDotGen

        return TemplateDotGen().visit(self)

    def _requires_semicolon(self):
        return False


class StringTemplate(TemplateNode):
    """
    A template node that wraps Python's string.Template.
    """
    def __init__(self, template_txt, child_dict):
        """
        Create a new template node.

        :param template_txt: The template as a string.
        :param child_dict: A mapping between template keys \
        and subtrees (CtreeNodes).
        """
        from textwrap import dedent
        dedented_txt = dedent(template_txt)

        from string import Template
        self._template = Template(dedented_txt)
        self._children = child_dict
        self._fields = child_dict.keys()

    def __getattr__(self, name):
        """Check in child_dict if 'name' is a child."""
        try:
            return self._children[name]
        except KeyError:
            pass
        raise AttributeError(name)

    # FIXME StringTemplate don't work with NodeTransformers very well
    # because the new, returned node isn't updated in the _children
    # dictionary.
