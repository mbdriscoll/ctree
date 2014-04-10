import unittest

from ctree.util import highlight
from util import PreventImport

class TestNoPygments(unittest.TestCase):
    def test_no_pygments(self):
        """ No pygments => no syntax highlighting. """
        with PreventImport('pygments'):
            code = "int a = 0;"
            highlighted = highlight(code, "c")
            self.assertEqual(code, highlighted)


class TestHighlights(unittest.TestCase):
    def test_highlight_c(self):
        highlighted = highlight("int a = 0;", "c")
        assert len(highlighted) > 0

    def test_highlight_llvm(self):
        highlighted = highlight("%add.i.1 = fadd double %14, %mul.i.1", "llvm")
        assert len(highlighted) > 0

    def test_bad_lang(self):
        with self.assertRaises(ValueError):
            highlight("int a = 0;", "not-a-language")
