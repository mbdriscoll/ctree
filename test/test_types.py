import ctypes

from ctree.types import get_ctype, get_common_ctype
from util import CtreeTest
from ctree.c.nodes import SymbolRef, FunctionDecl

class TestTypeRecognizer(CtreeTest):
    def test_int(self):
        ty = get_ctype(123)
        self.assertIsInstance(ty, ctypes.c_long)

    def test_float(self):
        ty = get_ctype(456.7)
        self.assertIsInstance(ty, ctypes.c_double)

    def test_char(self):
        ty = get_ctype("c")
        self.assertIsInstance(ty, ctypes.c_char)

    def test_none(self):
        ty = get_ctype(None)
        self.assertIsInstance(ty, type(None))

    def test_bool(self):
        ty = get_ctype(True)
        self.assertIsInstance(ty, ctypes.c_bool)

    def test_string(self):
        self.assertIsInstance(get_ctype("foo"),     ctypes.c_char_p)
        self.assertIsInstance(get_ctype(""),        ctypes.c_char_p)
        self.assertIsInstance(get_ctype("one two"), ctypes.c_char_p)

    def test_bad_type(self):
        class Bad(object): pass
        with self.assertRaises(ValueError):
            ty = get_ctype(Bad())


class TestTypeCodeGen(CtreeTest):
    def test_int(self):
        tree = SymbolRef("i", ctypes.c_int())
        self._check_code(tree, "int i")

    def test_long(self):
        tree = SymbolRef("i", ctypes.c_long())
        self._check_code(tree, "long i")

    def test_float(self):
        tree = SymbolRef("i", ctypes.c_double())
        self._check_code(tree, "double i")

    def test_char(self):
        tree = SymbolRef("i", ctypes.c_char())
        self._check_code(tree, "char i")

    def test_none(self):
        tree = SymbolRef("i", ctypes.c_void_p())
        self._check_code(tree, "void* i")

    def test_bool(self):
        tree = SymbolRef("i", ctypes.c_bool())
        self._check_code(tree, "bool i")

    def test_string(self):
        tree = SymbolRef("i", ctypes.c_char_p())
        self._check_code(tree, "char* i")

    def test_pointer(self):
        tree = SymbolRef("i", ctypes.POINTER(ctypes.c_double)())
        self._check_code(tree, "double* i")

    def test_none(self):
        tree = FunctionDecl(None, "foo", ())
        self._check_code(tree, "void foo()")

    def test_bad_type(self):
        class Bad(object): pass
        with self.assertRaises(ValueError):
            SymbolRef("i", Bad()).codegen()

class TestTypeCoercion(CtreeTest):
    def test_coercion(self):
        types = (ctypes.c_long, ctypes.c_double, ctypes.c_int)
        self.assertEqual(get_common_ctype(types), ctypes.c_double)
