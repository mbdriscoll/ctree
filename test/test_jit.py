import unittest

from ctree.jit import *
from fixtures import *

class TestJit(unittest.TestCase):

  def test_identity(self):
    mod = JitModule()
    mod.load(identity_ast)
    c_identity_fn = mod.get_callable(identity_ast)
    self.assertEqual(identity(1), c_identity_fn(1))
    self.assertEqual(identity(12), c_identity_fn(12))
    self.assertEqual(identity(123), c_identity_fn(123))

  def test_fib(self):
    mod = JitModule()
    mod.load(fib_ast)
    c_fib_fn = mod.get_callable(fib_ast)
    self.assertEqual(fib(1), c_fib_fn(1))
    self.assertEqual(fib(6), c_fib_fn(6))

  def test_gcd(self):
    mod = JitModule()
    mod.load(gcd_ast)
    c_gcd_fn = mod.get_callable(gcd_ast)
    self.assertEqual(gcd(44, 122), c_gcd_fn(44, 122))
    self.assertEqual(gcd(27, 39), c_gcd_fn(27, 39))
