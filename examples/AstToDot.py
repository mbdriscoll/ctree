from ctree.nodes import *

def main():
  stmt0 = Assign(SymbolRef('foo'), Constant(123.4))
  stmt1 = FunctionDecl(Float(), SymbolRef("bar"), [Int(), Long()])
  tree = File([stmt0, stmt1])
  print (tree.to_dot())

if __name__ == '__main__':
  main()
