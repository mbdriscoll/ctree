import unittest

from ctree.c.nodes import *
from ctree.c.types import *
import numpy


class TestTypeProperties(unittest.TestCase):
    def test_float_equality(self):
        self.assertEqual(Float(), Float())

    def test_unequality(self):
        self.assertNotEqual(Float(), Int())


class TestTypeFetcher(unittest.TestCase):
    def _check(self, actual, expected):
        self.assertEqual(actual, expected)

    def test_string_type(self):
        s = String("foo")
        self._check(s.get_type(), Ptr(Char()))

    def test_int_type(self):
        n = Constant(123)
        self._check(n.get_type(), Long())

    def test_float_type(self):
        n = Constant(123.4)
        self._check(n.get_type(), Double())

    def test_char_type(self):
        n = Constant('b')
        self._check(n.get_type(), Char())

    def test_binop_add_intint(self):
        a, b = Constant(1), Constant(2)
        node = Add(a, b)
        self._check(node.get_type(), Long())

    def test_binop_add_floatfloat(self):
        a, b = Constant(1.3), Constant(2.4)
        node = Add(a, b)
        self._check(node.get_type(), Double())

    def test_binop_add_floatint(self):
        a, b = Constant(1.3), Constant(2)
        node = Add(a, b)
        self._check(node.get_type(), Double())

    def test_binop_add_intfloat(self):
        a, b = Constant(1), Constant(2.3)
        node = Add(a, b)
        self._check(node.get_type(), Double())

    def test_binop_add_charint(self):
        a, b = Constant('b'), Constant(2)
        node = Add(a, b)
        self._check(node.get_type(), Long())

    def test_binop_add_charfloat(self):
        a, b = Constant('b'), Constant(2.3)
        node = Add(a, b)
        self._check(node.get_type(), Double())

    def test_binop_compare_lessthan(self):
        a, b = Constant('b'), Constant(2.3)
        node = Lt(a, b)
        self._check(node.get_type(), Int())

    def test_binop_compare_comma(self):
        a, b = Constant('b'), Constant(2.3)
        node = Comma(a, b)
        self._check(node.get_type(), Double())

    def test_bad_constant(self):
        class nothing:
            pass

        a = Constant(nothing())
        with self.assertRaises(Exception):
            self._check(a.get_type(), Int())

    class Nothing:
        pass

    def test_bad_type_coversion(self):
        with self.assertRaises(Exception):
            get_ctree_type(self.Nothing)

    def test_bad_obj_coversion(self):
        with self.assertRaises(Exception):
            get_ctree_type(self.Nothing())


class BadType(CtreeType):
    pass


class GoodType(CtreeType):

    def codegen(self):
        pass

    def as_ctypes(self):
        pass


class TestOverrideException(unittest.TestCase):

    def test_no_codegen(self):
        with self.assertRaises(Exception):
            BadType().codegen()

    def test_no_as_ctypes(self):
        with self.assertRaises(Exception):
            BadType().as_ctypes()

    def test_with_codegen(self):
        try:
            GoodType().codegen()
        except Exception:
            self.fail("codegen should not raise exception.")

    def test_with_as_ctypes(self):
        try:
            GoodType().as_ctypes()
        except Exception:
            self.fail("as_ctypes should not raise exception.")


class TestIntegerPromote(unittest.TestCase):

    def test_noop(self):
        self.assertEqual(CTypeFetcher._integer_promote(Int()), Int())

    def test_char(self):
        self.assertEqual(CTypeFetcher._integer_promote(Char()), Int())

    def test_short(self):
        self.assertEqual(CTypeFetcher._integer_promote(Short()), Int())

    def test_exception(self):
        with self.assertRaises(Exception):
            CTypeFetcher._integer_promote(Ptr())


class TestUsualArithmeticConvert(unittest.TestCase):

    def test_long_double(self):
        self.assertEqual(
            CTypeFetcher._usual_arithmetic_convert(LongDouble(), Int()),
            LongDouble()
        )

    def test_float(self):
        self.assertEqual(
            CTypeFetcher._usual_arithmetic_convert(Int(), Float()), Float()
        )

    def test_promotion_ulong(self):
        self.assertEqual(
            CTypeFetcher._usual_arithmetic_convert(Int(), ULong()), ULong()
        )

    def test_promotion_long(self):
        self.assertEqual(
            CTypeFetcher._usual_arithmetic_convert(Int(), Long()), Long()
        )

    def test_promotion_uint(self):
        self.assertEqual(
            CTypeFetcher._usual_arithmetic_convert(UInt(), Int()), UInt()
        )

    def test_promotion_int(self):
        self.assertEqual(
            CTypeFetcher._usual_arithmetic_convert(Char(), Int()), Int()
        )

    def test_promotion_Char(self):
        self.assertEqual(
            CTypeFetcher._usual_arithmetic_convert(Char(), Char()), Int()
        )


class TestPtr(unittest.TestCase):

    def test_ctype(self):
        p = Ptr(Char())
        self.assertEqual(p.as_ctype(), ctypes.POINTER(ctypes.c_char))


class TestNdPointer(unittest.TestCase):

    def test_get_base_type(self):
        ndp = NdPointer(numpy.double)
        self.assertEqual(ndp.get_base_type(), Double())

    def test_to(self):
        arr = numpy.ndarray((2, 2), numpy.float32)
        ndp = NdPointer.to(arr)
        self.assertEqual(ndp, NdPointer(numpy.float32, 2, (2, 2)))


class TestNPTypeResolver(unittest.TestCase):

    def test_long(self):
        type = NumpyTypeResolver.resolve(numpy.int64)
        self.assertEqual(type, Long())