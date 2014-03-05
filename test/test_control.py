import unittest

from ctree.c.nodes import *


class TestReturns(unittest.TestCase):
    def _check(self, tree, expected):
        actual = str(tree)
        self.assertEqual(actual, expected)

    def test_return_void(self):
        tree = Return()
        self._check(tree, "return")

    def test_return_int(self):
        tree = Return(Constant(1))
        self._check(tree, "return 1")

    def test_return_sym(self):
        tree = Return(SymbolRef('foo'))
        self._check(tree, "return foo")


class TestIfs(unittest.TestCase):
    def setUp(self):
        self.cond = Constant(1)
        self.then = [Assign(SymbolRef('foo'), SymbolRef('bar'))]
        self.elze = [Assign(SymbolRef('spam'), SymbolRef('eggs'))]

    def _check(self, tree, expected):
        actual = str(tree)
        self.assertEqual(actual, expected)

    def test_ifthen(self):
        tree = If(self.cond, self.then)
        self._check(tree, """if (1) {
    foo = bar;
}""")

    def test_ifthenelse(self):
        tree = If(self.cond, self.then, self.elze)
        self._check(tree, """if (1) {
    foo = bar;
} else {
    spam = eggs;
}""")


class TestWhiles(unittest.TestCase):
    def setUp(self):
        self.cond = Constant(2)
        self.body = [SymbolRef('foo')]

    def _check(self, tree, expected):
        actual = str(tree)
        self.assertEqual(actual, expected)

    def test_while(self):
        tree = While(self.cond, self.body)
        self._check(tree, """while (2) {
    foo;
}""")

    def test_dowhile(self):
        tree = DoWhile(self.body, self.cond)
        self._check(tree, """do {
    foo;
} while (2)""")


class TestFor(unittest.TestCase):
    def _check(self, tree, expected):
        actual = str(tree)
        self.assertEqual(actual, expected)

    def test_for_00(self):
        init = Assign(SymbolRef("foo"), Constant(0))
        test = Lt(SymbolRef("foo"), Constant(10))
        incr = PostInc(SymbolRef("foo"))
        body = [FunctionCall(SymbolRef("printf"), [SymbolRef("foo")])]
        tree = For(init, test, incr, body)
        self._check(tree, """for (foo = 0; foo < 10; foo ++) {
    printf(foo);
}""")
