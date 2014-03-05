import unittest


class TestImport(unittest.TestCase):
    def test_import_base(self):
        import ctree

    def test_import_nodes(self):
        import ctree.c.nodes
