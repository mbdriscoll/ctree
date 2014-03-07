import abc

from ctree.nodes import CtreeNode
from ctree.visitors import NodeVisitor


class CtreeType(CtreeNode):
    def codegen(self, indent=0):
        raise Exception("%s should override codegen()" % type(self))

    def as_ctypes(self):
        raise Exception("%s should override as_ctypes()" % type(self))

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))


class TypeFetcher(NodeVisitor):
    """
    Dynamically computes the type of the Expression.
    """
    pass


class CtreeTypeResolver(object):
    __metaclass__ = abc.ABCMeta

    @staticmethod
    @abc.abstractmethod
    def resolve(obj):
        pass


def get_ctree_type(obj):
    from ctree.c.types import CTypeResolver, NumpyTypeResolver

    for resolver in [CTypeResolver(), NumpyTypeResolver()]:
        ty = resolver.resolve(obj)
        if ty is not None:
            return ty
    raise Exception("Unable to resolve type for %s." % repr(obj))
