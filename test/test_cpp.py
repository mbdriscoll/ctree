import unittest

from ctree.cpp.nodes import *


class TestCppIncludes(unittest.TestCase):
    def test_include_angled(self):
        tree = CppInclude("foo.h")
        self.assertEqual(str(tree), "#include <foo.h>")

    def test_include_quotes(self):
        tree = CppInclude("foo.h", angled_brackets=False)
        self.assertEqual(str(tree), '#include "foo.h"')
