from ctree.nodes import AstNode

class NodeVisitor(object):
  """
  Call visit_Foo(node) method for each node type Foo. See Python's
  ast.NodeVisitor class for more details.
  """
  def visit(self, node):
    """Visit a node."""
    method = 'visit_' + node.__class__.__name__
    visitor = getattr(self, method, self.generic_visit)
    return visitor(node)

  def generic_visit(self, node):
    """Called if no explicit visitor function exists for a node."""
    for field, value in node.children():
      if isinstance(value, list):
        for item in value:
          if isinstance(item, AstNode):
            self.visit(item)
      elif isinstance(value, AstNode):
        self.visit(value)


class NodeTransformer(NodeVisitor):
  """
  Call visit_Foo(node) method for each node type Foo, and assign the
  return value to the field. See Python's ast.NodeTransformer class
  for more details.
  """
  def generic_visit(self, node):
    for field, old_value in node.children():
      old_value = getattr(node, field, None)
      if isinstance(old_value, list):
        new_values = []
        for value in old_value:
          if isinstance(value, AST):
            value = self.visit(value)
            if value is None:
              continue
            elif not isinstance(value, AST):
              new_values.extend(value)
              continue
          new_values.append(value)
        old_value[:] = new_values
      elif isinstance(old_value, AST):
        new_node = self.visit(old_value)
        if new_node is None:
          delattr(node, field)
        else:
          setattr(node, field, new_node)
    return node
