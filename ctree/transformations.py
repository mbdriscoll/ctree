import ast

from ctree.nodes.c import *
from ctree.types import *
from ctree.visitors import NodeTransformer

def _eval_ast(tree):
  """Evaluate the given subtree as a python expression."""
  return eval(compile(ast.Expression(tree), __name__, 'eval'))

class PyCtxScrubber(NodeTransformer):
  """
  Removes pesky ctx attributes from Python ast.Name nodes,
  yielding much cleaner python asts.
  """
  def visit_Name(self, node):
    node.ctx = None
    return node


class PyBasicConversions(NodeTransformer):
  """
  Convert constructs with obvious C analogues.
  """
  PY_OP_TO_CTREE_OP = {
    ast.Add:     Op.Add,
    ast.Mult:    Op.Mul,
    ast.Sub:     Op.Sub,
    ast.Lt:      Op.Lt,
    # TODO list the rest
  }

  def visit_Num(self, node):
    return Constant(node.n)

  def visit_Str(self, node):
    return String(node.s)

  def visit_Name(self, node):
    return SymbolRef(node.id)

  def visit_BinOp(self, node):
    lhs = self.visit(node.left)
    rhs = self.visit(node.right)
    op = self.PY_OP_TO_CTREE_OP[type(node.op)]()
    return BinaryOp(lhs, op, rhs)

  def visit_Return(self, node):
    assert isinstance(node, ast.Return)
    val = self.visit(node.value)
    return Return(val)

  def visit_If(self, node):
    assert isinstance(node, ast.If)
    cond = self.visit(node.test)
    then = [self.visit(t) for t in node.body]
    elze = [self.visit(t) for t in node.orelse] or None
    return If(cond, then, elze)

  def visit_Compare(self, node):
    assert len(node.ops) == 1, \
      "PyBasicConversions doesn't support Compare nodes with more than one operator."
    lhs = self.visit(node.left)
    op = self.PY_OP_TO_CTREE_OP[type(node.ops[0])]()
    rhs = self.visit(node.comparators[0])
    return BinaryOp(lhs, op, rhs)

  def visit_Module(self, node):
    body = [self.visit(s) for s in node.body]
    return File(body)

  def visit_Call(self, node):
    args = [self.visit(a) for a in node.args]
    fn = self.visit(node.func)
    return FunctionCall(fn, args)

  def visit_FunctionDef(self, node):
    params = [self.visit(p) for p in node.args.args]
    defn = [self.visit(s) for s in node.body]
    return FunctionDecl(node.returns, node.name, params, defn)

  def visit_arg(self, node):
    return SymbolRef(node.arg, node.annotation)


class PyTypeRecognizer(NodeTransformer):
  """
  Convert types in function annotations to ctree types.
  """
  def visit_arg(self, node):
    if node.annotation:
      node.annotation = py_type_to_ctree_type( _eval_ast(node.annotation) )
    return self.generic_visit(node)

  def visit_FunctionDef(self, node):
    if node.returns:
      node.returns = py_type_to_ctree_type( _eval_ast(node.returns) )
    return self.generic_visit(node)


class FixUpParentPointers(NodeTransformer):
  """
  Add parent pointers if they're missing.
  """
  def generic_visit(self, node):
    for fieldname, child in ast.iter_fields(node):
      if type(child) is list:
        for grandchild in child:
          setattr(grandchild, 'parent', node)
          self.visit(grandchild)
      elif isinstance(child, ast.AST):
        setattr(child, 'parent', node)
        self.visit(child)
    return node
