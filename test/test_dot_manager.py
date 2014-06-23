__author__ = 'Chick Markley'

import unittest

from ctree.visual.dot_manager import DotManager
from inspect import getsource
from ctree.frontend import get_ast
from fixtures.sample_asts import *

# TODO: This test is failing for some strange reason
# def square_of(n):
#     return n * n

# class TestDotManager(unittest.TestCase):
#     """
#     Difficult to test because of ipython and dot dependencies
#     """

#     def test_c_identity(self):
#         tree = get_ast(getsource(square_of))
#         DotManager.run_dot(tree)

