import unittest

from ctree.nodes.c import *
from ctree.analyses import *
from fixtures import *

class TestVerifyParentPointers(unittest.TestCase):

  def test_identity(self):
    VerifyParentPointers().visit( identity_ast )

  def test_fib(self):
    VerifyParentPointers().visit( fib_ast )

  def test_gcd(self):
    VerifyParentPointers().visit( gcd_ast )

  def test_raise_identity(self):
    identity_ast.find(SymbolRef, name="x").parent = None
    with self.assertRaises(AstValidationError):
      VerifyParentPointers().visit( identity_ast )

  def test_raise_fib(self):
    fib_ast.find(Constant, value=2).parent = None
    with self.assertRaises(AstValidationError):
      VerifyParentPointers().visit( fib_ast )

  def test_raise_gcd(self):
    gcd_ast.find(Return).parent = None
    with self.assertRaises(AstValidationError):
      VerifyParentPointers().visit( gcd_ast )
