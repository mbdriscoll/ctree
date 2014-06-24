"""
Illustrates the DOT-printing functionality by constructing
a small AST and printing its DOT representation.

Usage:
  $ python AstToDot.py > graph.dot

The resulting file can be viewed with a visualizer like Graphiz.
"""

from ctypes import *
from ctree.nodes import *
from ctree.c.nodes import *


def main():
    stmt0 = Assign(SymbolRef('foo'), Constant(123.4))
    stmt1 = FunctionDecl(c_float(), SymbolRef("bar"), [
        SymbolRef("spam", c_int()), SymbolRef("eggs", c_long())], [String("baz")])
    stmt3 = [[SymbolRef("abc")]]
    tree = CFile("myfile", [stmt0, stmt1, stmt3])
    print (tree.to_dot())


if __name__ == '__main__':
    main()
