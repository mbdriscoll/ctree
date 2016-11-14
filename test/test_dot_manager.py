__author__ = 'Chick Markley'

import unittest

from ctree.visual.dot_manager import DotManager
from ctree.frontend import get_ast


def square_of(n):
    return n * n

class TestDotManager(unittest.TestCase):
    """
    Difficult to test because of ipython and dot dependencies
    """

    @unittest.skip("difficult to test because of ipython and dot dependencies")
    def test_c_identity(self):
        tree = get_ast(square_of)
        DotManager.run_dot(tree.to_dot())


