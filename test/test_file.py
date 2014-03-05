import unittest

from ctree.c.nodes import *
from ctree.c.types import *


class TestFile(unittest.TestCase):
    def _check(self, tree, expected):
        actual = str(tree)
        self.assertEqual(actual, expected)

    def test_simple_00(self):
        foo = SymbolRef("foo", sym_type=Int())
        bar = FunctionDecl(Float(), SymbolRef("bar"))
        tree = CFile("myfile", [foo, bar])
        self._check(tree, """\
// <file: myfile.c>
int foo;
float bar();
""")
