import unittest

from ctree.c.macros import *


class TestCMacrosCodegen(unittest.TestCase):
    def test_null(self):
        node = NULL()
        self.assertEqual(str(node), "NULL")

    def test_printf(self):
        node = printf("%s %s", SymbolRef("x"), SymbolRef("y"))
        self.assertEqual(str(node), "printf(\"%s %s\", x, y)")
