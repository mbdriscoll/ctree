from ctypes import *

from util import CtreeTest
from ctree.c.nodes import *


class TestFile(CtreeTest):
    def test_simple_00(self):
        foo = SymbolRef("foo", sym_type=c_int())
        bar = FunctionDecl(c_double(), SymbolRef("bar"))
        tree = CFile("myfile", [foo, bar])
        self._check_code(tree, """\
        // <file: myfile.c>
        int foo;
        double bar();
        """)
