"""
Illustrates the DOT-printing functionality by constructing
a small AST and printing its DOT representation.

Usage:
  $ python AstToDot.py > graph.dot

The resulting file can be viewed with a visualizer like Graphiz.
"""

from ctree.ast import *
from ctree.c.nodes import *
from ctree.c.types import *

from ctree.dotgen import to_dot

def main():
  stmt0 = Assign(SymbolRef('foo'), Constant(123.4))
  stmt1 = FunctionDecl(Float(), SymbolRef("bar"), [
            SymbolRef("spam", Int()), SymbolRef("eggs", Long())], [String("baz")])
  tree = CFile("myfile", [stmt0, stmt1])
  print (to_dot(tree))

if __name__ == '__main__':
  main()
