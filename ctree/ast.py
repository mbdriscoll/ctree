"""
Defines the hierarchy of AST nodes.
"""

import ast
import ctypes as ct

from ctree.codegen import CodeGenVisitor
from ctree.dotgen import DotGenVisitor

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
    raise Exception("Node class %s should override codegen()" % type(self))

  def _to_dot(self):
    """Retrieve the AST in DOT format for vizualization."""
    raise Exception("Node class %s should override _to_dot()" % type(self))

  def _requires_semicolon(self):
    """When coverted to a string, this node should be followed by a semicolon."""
    return True

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
      elif isinstance(child, list) and self in child:
        child[ child.index(self) ] = new_node
    return new_node

  def insert_before(self, older_sibling):
    """
    Insert the given node just before 'self' in the current scope. Requires
    that 'self' be contained in a list.
    """
    parent = self.parent
    assert self.parent, "Tried to insert_before a node without a parent."
    for fieldname, child in ast.iter_fields(parent):
      if isinstance(child, list) and self in child:
        child.insert(child.index(self), older_sibling)
        return
    raise Exception("Couldn't perform insertion.")

  def insert_after(self, younger_sibling):
    """
    Insert the given node just before 'self' in the current scope. Requires
    that 'self' be contained in a list.
    """
    parent = self.parent
    assert self.parent, "Tried to insert_before a node without a parent."
    for fieldname, child in ast.iter_fields(parent):
      if isinstance(child, list) and self in child:
        child.insert(child.index(self)+1, younger_sibling)
        return
    raise Exception("Couldn't perform insertion.")

# ---------------------------------------------------------------------------
# Common nodes

class CommonNode(CtreeNode):
  """Miscellaneous IR nodes."""
  def codegen(self, indent=0):
    return CommonCodeGen(indent).visit(self)

  def _to_dot(self):
    return CommonDotGen().visit(self)


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


class CommonCodeGen(CodeGenVisitor):
  """Manages conversion of all common nodes to txt."""
  def visit_File(self, node):
    return ";\n".join(map(str, node.body)) + ";\n"


class CommonDotGen(DotGenVisitor):
  """Manages coversion of all common nodes to dot."""
  pass
