from copy import deepcopy

from util import CtreeTest
from fixtures.sample_asts import *
from ctree.transformations import Lifter

class TestLifter(CtreeTest):
    def test_nop(self):
        for py_fn, tree in SAMPLE_ASTS:
            transformed = Lifter().visit(deepcopy(tree))
            self._check_code(actual=tree, expected=transformed)

    def test_one_param(self):
        inner = SymbolRef("foo")
        inner.lift(params=[SymbolRef(inner.name, c_int())])

        tree = FunctionDecl(None, "fn", [], [
            Assign(inner, Constant(123)),
        ])

        tree = Lifter().visit(tree)

        self._check_code(actual=tree, expected="""\
        void fn(int foo) {
            foo = 123;
        }""")

    def test_two_params(self):
        inner0 = SymbolRef("foo")
        inner0.lift(params=[SymbolRef(inner0.name, c_int())])

        inner1 = SymbolRef("bar")
        inner1.lift(params=[SymbolRef(inner1.name, c_double())])

        tree = FunctionDecl(None, "fn", [], [
            Assign(inner0, Constant(123)),
            Assign(inner1, Constant(456.7)),
        ])

        tree = Lifter().visit(tree)

        self._check_code(actual=tree, expected="""\
        void fn(int foo, double bar) {
            foo = 123;
            bar = 456.7;
        }""")

    def test_one_include(self):
        tree = CFile("generated", [deepcopy(get_two_ast)])
        stmt = tree.find(FunctionDecl).defn[0]
        stmt.lift(includes=[CppInclude("stdio.h")])

        tree = Lifter().visit(tree)

        self._check_code(actual=tree, expected="""\
        // <file: generated.c>
        #include <stdio.h>
        long get_two() {
            return 2;
        };
        """)

    def test_multi_includes(self):
        tree = CFile("generated", [deepcopy(get_two_ast)])
        stmt0 = tree.find(FunctionDecl)
        stmt1 = stmt0.defn[0]

        stmt0.lift(includes=[CppInclude("stdio.h")])
        stmt1.lift(includes=[CppInclude("stdlib.h"), CppInclude("float.h")])

        tree = Lifter().visit(tree)

        self._check_code(actual=tree, expected="""\
        // <file: generated.c>
        #include <stdio.h>
        #include <stdlib.h>
        #include <float.h>
        long get_two() {
            return 2;
        };
        """)
