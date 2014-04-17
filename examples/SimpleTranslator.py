"""
Parses the python AST below, transforms it to C, JITs it, and runs it.
"""

import logging

logging.basicConfig(level=20)

import numpy as np

from ctree.c.types import FuncType
from ctree.transformations import *
from ctree.frontend import get_ast
from ctree.jit import LazySpecializedFunction
from ctree.jit import ConcreteSpecializedFunction
from ctree.types import get_ctree_type


def fib(n):
    if n < 2:
        return n
    else:
        return fib(n - 1) + fib(n - 2)


class BasicFunction(ConcreteSpecializedFunction):
    def __init__(self, entry_name, project_node, entry_typesig):
        self._c_function = self._compile(entry_name, project_node, entry_typesig)

    def __call__(self, *args, **kwargs):
        return self._c_function(*args, **kwargs)


class BasicTranslator(LazySpecializedFunction):
    def __init__(self, func):
        super(BasicTranslator, self).__init__(get_ast(func))

    def args_to_subconfig(self, args):
        return {'arg_type': get_ctree_type(args[0])}

    def transform(self, tree, program_config):
        """Convert the Python AST to a C AST."""
        tree = PyBasicConversions().visit(tree)

        fib_fn = tree.find(FunctionDecl, name="fib")
        fib_arg_type = program_config[0]['arg_type']
        fib_type = FuncType(fib_arg_type, [fib_arg_type])
        fib_fn.set_typesig(fib_type)

        return BasicFunction(fib_fn.name, tree, fib_type.as_ctype())


def main():
    c_fib = BasicTranslator(fib)

    assert fib(10) == c_fib(10)
    assert fib(11) == c_fib(11)
    assert fib(12) == c_fib(12)
    assert fib(13) == c_fib(13)

    assert fib(13.3) == c_fib(13.3)
    assert fib(13.4) == c_fib(13.4)
    assert fib(13.5) == c_fib(13.5)
    assert fib(13.6) == c_fib(13.6)

    assert fib(14) == c_fib(14)
    assert fib(13.7) == c_fib(13.7)

    print ("Success.")


if __name__ == '__main__':
    main()
