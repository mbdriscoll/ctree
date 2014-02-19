"""
Defines the hierarchy of AST nodes.

"""

import logging

class AstNode(object):
  """Base class for all AST nodes in ctree."""
  def __init__(self):
    self.parent = None
  def __setattr__(self, name, value):
    """Set attribute and preserve parent pointers."""
    if isinstance(value, AstNode):
      value.parent = self
    if isinstance(value, list):
      for grandchild in value:
        if isinstance(grandchild, AstNode):
          grandchild.parent = self
    object.__setattr__(self, name, value)

  def __str__(self):
    return self._codegen()

class Statement(AstNode):
  """Section B.2.3 6.6."""
  pass

class JumpStatement(Statement):
  """Section B.2.3 6.6.6."""
  pass

class ReturnStatement(Statement):
  """Seciton B.2.3 6.6.6 line 4."""
  def __init__(self, value=None):
    self.value = value

class Token(AstNode):
  """Section B.1.1 6.1."""
  pass

class Constant(Token):
  """Section B.1.4 6.1.3."""
  def __init__(self, value):
    self.value = value

class Float(Constant):
  """Section B.1.4 6.1.3.1."""
  def __init__(self, value):
    super().__init__(value)

  def _codegen(self):
    return "%g" % self.value

class Int(Constant):
  """Section B.1.4 6.1.3.1."""
  def __init__(self, value):
    if not isinstance(value, int):
      logging.warn("creating an Int constant with a non-int-type argument.")
    super().__init__(value)

  def _codegen(self):
    return "%d" % self.value

class Char(Constant):
  """Section B.1.4 6.1.3.1."""
  def __init__(self, value):
    if not(isinstance(value, str) and len(value) == 1):
      logging.error("char constants require length-1 python strings to create.")
    super().__init__(value)

  def _codegen(self):
    return "'%s'" % self.value
