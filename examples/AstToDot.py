"""
Illustrates the DOT-printing functionality by constructing
a small AST and printing its DOT representation.

Usage:
  $ python AstToDot.py > graph.dot

The resulting file can be viewed with a visualizer like Graphiz.
"""

import ctypes as ct
from ctree.nodes.c import *

def main():
  stmt0 = Assign(SymbolRef('foo'), Constant(123.4))
  stmt1 = FunctionDecl(ct.c_float, SymbolRef("bar"), [Param(ct.c_int), Param(ct.c_long)], [String("baz")])
  tree = File([stmt0, stmt1])
  print (tree.to_dot())

if __name__ == '__main__':
  main()
