import unittest

from ctree.nodes.c import *

class TestFile(unittest.TestCase):

  def _check(self, tree, expected):
    actual = str(tree)
    self.assertEqual(actual, expected)

  def test_simple_00(self):
    foo = SymbolRef("foo", type=Int())
    bar = FunctionDecl(Float(), SymbolRef("bar"))
    tree = File([foo, bar])
    self._check(tree, """\
int foo;
float bar();
""")