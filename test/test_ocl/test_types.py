import unittest

from ctree.c.nodes import SymbolRef
from ctree.ocl.types import *

class TestOclCodegen(unittest.TestCase):

  def _check(self, tree, expected):
    actual = str(tree)
    self.assertEqual(actual, expected)

  def test_cl_device_id(self):
    self._check(SymbolRef("foo", cl_device_id()), "cl_device_id foo")

  def test_cl_context(self):
    self._check(SymbolRef("foo", cl_context()), "cl_context foo")

  def test_cl_command_queue(self):
    self._check(SymbolRef("foo", cl_command_queue()), "cl_command_queue foo")

  def test_cl_program(self):
    self._check(SymbolRef("foo", cl_program()), "cl_program foo")

  def test_cl_kernel(self):
    self._check(SymbolRef("foo", cl_kernel()), "cl_kernel foo")

  def test_cl_mem(self):
    self._check(SymbolRef("foo", cl_mem()), "cl_mem foo")

  def test_cl_mem_dot(self):
    from ctree.dotgen import to_dot
    to_dot(SymbolRef("foo", cl_mem()))
