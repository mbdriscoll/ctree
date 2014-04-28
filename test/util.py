import unittest
import difflib
import textwrap

from ctree.util import highlight

class PreventImport(object):
    """
    Context manager that overrides the builtin __import__ method.
    Throws ImportError whenever 'target' is in the name of the
    module to be imported. This is useful for testing functions
    that try to import a module and do different things if it
    succeeds.

    For example:
        >>> with PreventImport("scipy"):
        ...     import scipy.sparse
        ...
        Traceback (most recent call last):
          File "<stdin>", line 2, in <module>
          File "util.py", line 16, in __call__
            raise ImportError("suppressed import of %s" % name)
        ImportError: suppressed import of scipy.sparse 
    """
    def __init__(self, target):
        self.target = target

    def __call__(self, name, *args, **kwargs):
        if self.target in name:
            raise ImportError("suppressed import of %s" % name)
        else:
            return self.__import__(name, *args, **kwargs)

    def __enter__(self):
        self.__import__ = __builtins__['__import__']
        __builtins__['__import__'] = self

    def __exit__(self, excp, traceback, value):
        __builtins__['__import__'] = self.__import__


class CtreeTest(unittest.TestCase):
    def _check_code(self, actual="", expected=""):
        if not isinstance(actual, str):
            actual = textwrap.dedent( str(actual) )
        if not isinstance(expected, str):
            expected = textwrap.dedent( str(expected) )

        actual   = textwrap.dedent(str(actual))
        expected = textwrap.dedent(str(expected))

        if actual != expected:
            actual_display = (actual + ("\n" if actual[-1] != "\n" else "")).splitlines(True)
            expected_display = expected.splitlines(True)
            diff_gen = difflib.unified_diff(
                actual_display, expected_display,
                "<actual>", "<expected>")
            diff = "".join(diff_gen)
            print highlight(diff, language='diff')

        self.assertEqual(actual, expected)
