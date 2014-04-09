import unittest

from ctree.cpp.nodes import *
from ctree.c.nodes import Add, SymbolRef, Constant


class TestCppIncludes(unittest.TestCase):
    def test_include_angled(self):
        tree = CppInclude("foo.h")
        self.assertEqual(str(tree), "#include <foo.h>")

    def test_include_quotes(self):
        tree = CppInclude("foo.h", angled_brackets=False)
        self.assertEqual(str(tree), '#include "foo.h"')

class TestDefines(unittest.TestCase):
    def _check(self, node, expected_string):
        self.assertEqual(str(node), expected_string)

    def test_simple_macro(self):
        d1, d2 = SymbolRef("d1"), SymbolRef("d2")
        node = CppDefine("test_macro", [d1, d2], Add(d1, d2))
        self._check(node, "#define test_macro(d1, d2) (d1 + d2)")

    def test_no_args(self):
        node = CppDefine("test_macro", [], Constant(39))
        self._check(node, "#define test_macro() (39)")
