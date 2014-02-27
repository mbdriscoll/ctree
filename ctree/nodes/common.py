"""
Defines the hierarchy of AST nodes.
"""

import ast
import ctypes as ct

from ctree.codegen import CodeGenVisitor

class CtreeNode(ast.AST):
  """Base class for all AST nodes in ctree."""
  _fields = []

  def __init__(self, parent=None):
    """Initialize a new AST Node."""
    super().__init__()
    self.parent = parent

  def __setattr__(self, name, value):
    """Set attribute and preserve parent pointers."""
    if name != "parent":
      if isinstance(value, CtreeNode):
        value.parent = self
      elif isinstance(value, list):
        for grandchild in value:
          if isinstance(grandchild, CtreeNode):
            grandchild.parent = self
    super().__setattr__(name, value)

  def __str__(self):
    return self.codegen()

  def codegen(self, indent=0):
    raise Exception("Node class should override codegen()")

  def to_dot(self):
    """Retrieve the AST in DOT format for vizualization."""
    from ctree.dotgen import DotGenerator
    return DotGenerator().generate_from(self)

  def get_root(self):
    """
    Traverse the parent pointer list to find the eldest
    parent without a parent, aka the root.
    """
    root = self
    while root.parent != None:
      root = root.parent
    return root

  def find_all(self, node_class, **kwargs):
    """
    Returns a generator that yields all nodes of type
    'node_class' type whose attributes match those specified
    in kwargs. For example, all FunctionDecls with name 'fib'
    can be accessed via:
    >>> my_ast.find_all(FunctionDecl, name="fib")
    """
    def pred(node):
      if type(node) == node_class:
        for attr, value in kwargs.items():
          try:
            if getattr(node, attr) != value:
              break
          except AttributeError:
            break
        else:
          return True
      return False
    return self.find_if(pred)

  def find(self, node_class, **kwargs):
    """
    Returns one node of type 'node_class' whose attributes
    match those specified in kwargs, or None if no nodes
    can be found.
    """
    matching = self.find_all(node_class, **kwargs)
    try:
      return next(matching)
    except StopIteration:
      return None

  def find_if(self, pred):
    """
    Returns all nodes satisfying the given predicate,
    or None if no satisfactory nodes are found. The search
    starts from the current node.
    """
    for node in ast.walk(self):
      if pred(node):
        yield node

  def replace(self, new_node):
    """
    Replace the current node with 'new_node'.
    """
    parent = self.parent
    assert self.parent, "Tried to replace a node without a parent."
    for fieldname, child in ast.iter_fields(parent):
      if child is self:
        setattr(parent, fieldname, new_node)
    return new_node


# ---------------------------------------------------------------------------
# Common nodes

class CommonNode(CtreeNode):
  """Miscellaneous IR nodes."""
  def codegen(self, indent=0):
    return CommonCodeGen(indent).visit(self)

class Project(CommonNode):
  """Holds a list files."""
  _fields = ['files']
  def __init__(self, files=[]):
    self.files = files
    super().__init__()


class File(CommonNode):
  """Holds a list of statements."""
  _fields = ['body']
  def __init__(self, body=[]):
    self.body = body
    super().__init__()


# ---------------------------------------------------------------------------
# Common node code gen

class CommonCodeGen(CodeGenVisitor):
  """Manages conversion of all common nodes to txt."""
  def visit_File(self, node):
    return ";\n".join(map(str, node.body)) + ";\n"
