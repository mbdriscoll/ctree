import unittest

from ctree.dotgen import to_dot
from ctree.frontend import get_ast
from fixtures import *

class TestDotGen(unittest.TestCase):
  """
  Run the to_dot function on the fixture ASTs. There isn't
  a good way to check if the output is a legal DOT file,
  but we can at least ensure that the routine runs without
  throwing an exception.
  """

  def test_c_identity(self):
    self.assertNotEqual(to_dot(identity_ast), "")

  def test_c_gcd(self):
    self.assertNotEqual(to_dot(gcd_ast), "")

  def test_c_fib(self):
    self.assertNotEqual(to_dot(fib_ast), "")

  def test_py_identity(self):
    self.assertNotEqual(to_dot(get_ast(identity)), "")

  def test_py_gcd(self):
    self.assertNotEqual(to_dot(get_ast(gcd)), "")

  def test_py_fib(self):
    self.assertNotEqual(to_dot(get_ast(fib)), "")
