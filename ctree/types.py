from __future__ import absolute_import

import types
import sys

import ctypes
from ctypes import *

import logging

from ctree import _TYPE_CODEGENERATORS as generators
from ctree import _TYPE_RECOGNIZERS as recognizers

log = logging.getLogger(__name__)


def register_type_codegenerators(codegen_dict):
    """
    Registers routines for generating code for types.

    :param codegen_dict: Maps type classes to functions that
    take an instance of that class and return the corresponding
    string.
    """
    if sys.version_info >= (3, 0):
        existing_keys = generators.keys()
        new_keys = codegen_dict.keys()
    else:
        existing_keys = generators.viewkeys()
        new_keys = codegen_dict.viewkeys()
    intersection = existing_keys & new_keys
    if intersection:
        log.warning("replacing existing type_codegenerator for %s",
                    intersection)

    for genfn in generators.values():
        assert callable(genfn), "Found a non-callable type_codegen: %s" % genfn

    generators.update(codegen_dict)


def register_type_recognizers(typerec_dict):
    """
    Registers routines for getting ctypes objects from Python objects.

    :param typerec_dict: Maps Python classes to functions that
    take an instance of that class and return the corresponding
    ctypes object.
    """
    if sys.version_info >= (3, 0):
        existing_keys = recognizers.keys()
        new_keys = typerec_dict.keys()
    else:
        existing_keys = recognizers.viewkeys()
        new_keys = typerec_dict.viewkeys()
    intersection = existing_keys & new_keys
    if intersection:
        log.warning("replacing existing type_recognizer for %s", intersection)

    for genfn in recognizers.values():
        assert callable(genfn), "Found a non-callable type_codegen: %s" % genfn

    recognizers.update(typerec_dict)


def get_ctype(py_obj):
    """
    Given a python object, this routine tries to return the
    closest ctype type instance corresponding to that object.

    :param py_obj: A python object.
    """
    bases = [type(py_obj)]
    while bases:
        base = bases.pop()
        bases += base.__bases__
        try:
            return recognizers[base](py_obj)
        except KeyError:
            pass
    raise ValueError("No type recognizer defined for %s." % type(py_obj))

def get_c_type_from_numpy_dtype(dtype_specified):
        """
        Get the ctype corresponding to a given numpy.dtype
        :param: dtype_specified - the numpy.dtype
        :return: the ctype corresponding the the dtype_specified. None unable to match
        """
        typemap = {}
        for t in (c_byte, c_short, c_int, c_long, c_longlong):
            typemap["<i%s" % sizeof(t)] = t.__ctype_le__
            typemap[">i%s" % sizeof(t)] = t.__ctype_be__
        for t in (c_ubyte, c_ushort, c_uint, c_ulong, c_ulonglong):
            typemap["<u%s" % sizeof(t)] = t.__ctype_le__
            typemap[">u%s" % sizeof(t)] = t.__ctype_be__
        for t in (c_float, c_double):
            typemap["<f%s" % sizeof(t)] = t.__ctype_le__
            typemap[">f%s" % sizeof(t)] = t.__ctype_be__
        typemap["|b1"] = c_bool
        typemap["|i1"] = c_byte
        typemap["|u1"] = c_ubyte

        if dtype_specified.descr[0][1] in typemap:
            return typemap[dtype_specified.descr[0][1]]
        else:
            return None

def codegen_type(ctype):
    """
    Unparses the given ctype.

    :param ctype: A ctype type instance to be unparsed.
    """
    assert not isinstance(ctype, type), \
        "Expected a ctypes type instance, not %s, (%s):" % (ctype, type(ctype))

    bases = [type(ctype)]
    while bases:
        base = bases.pop()
        bases.extend(base.__bases__)
        try:
            val = generators[base](ctype)
            return val
        except KeyError:
            pass
    raise ValueError("No code generator defined for %s." % type(ctype))

def get_common_ctype(ctypes_list):
    """
    :param ctypes_list: iterable of ctypes
    :return: calculates the proper ctype for coercion of all types, as per

        If either is      long          double the other is promoted to      long          double
        If either is                    double the other is promoted to                    double
        If either is                    float  the other is promoted to                    float
        If either is long long unsigned int    the other is promoted to long long unsigned int
        If either is long long          int    the other is promoted to long long          int
        If either is long      unsigned int    the other is promoted to long      unsigned int
        If either is long               int    the other is promoted to long               int
        if either is           unsigned int    the other is promoted to           unsigned int
        If either is                    int    the other is promoted to                    int
        Both operands are promoted to int
    """

    #lowest ranking takes precedence
    rankings = [ctypes.c_longdouble, ctypes.c_double, ctypes.c_float, ctypes.c_long, ctypes.c_uint, ctypes.c_int, ctypes.c_byte,
                ctypes.c_wchar, ctypes.c_char, ctypes.c_bool, ctypes.c_void_p]
    filtered = []
    for c_type in ctypes_list:
        if c_type not in rankings:
            return c_type
        filtered.append(c_type)
    if filtered:
        return min(filtered, key=rankings.index)
    else:
        return ctypes.c_void_p