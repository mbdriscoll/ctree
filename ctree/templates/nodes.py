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
        from string import Template
        from collections import namedtuple

        dedented_txt = dedent(template_txt)
        self._template = Template(dedented_txt)
        self._children = child_dict
        self._fields = child_dict.keys()
        super(StringTemplate, self).__init__()

    def __setattr__(self, name, val):
        from ctree.nodes import CtreeNode

        if name == "_children":
            # set parent pointers in child_dict
            assert isinstance(val, dict)
            super(StringTemplate, self).__setattr__(name, val)
            for name, child in val.items():
                child.parent = self
        elif hasattr(self, "_children") and name in self._children:
            # insert into _children dictionary and set parent pointers
            self._children[name] = val
            if isinstance(val, CtreeNode):
                val.parent = self
        else:
            # do standard attribute resolution
            super(StringTemplate, self).__setattr__(name, val)

    def __getattr__(self, name):
        if name != "_children" and name in self._children:
            child = self._children[name]
            assert child.parent == self, "Encountered bad parent pointer to %s." % repr(child.parent)
            return self._children[name]
        raise AttributeError("'%s' has no attribute '%s'" % (type(self).__name__, name))
