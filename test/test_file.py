import unittest
import ctypes as ct

from ctree.nodes.common import *
from ctree.c.nodes import *

class TestFile(unittest.TestCase):

  def _check(self, tree, expected):
    actual = str(tree)
    self.assertEqual(actual, expected)

  def test_simple_00(self):
    foo = SymbolRef("foo", type=ct.c_int)
    bar = FunctionDecl(ct.c_float, SymbolRef("bar"))
    tree = File([foo, bar])
    self._check(tree, """\
int foo;
float bar();
""")
