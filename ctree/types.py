import ctypes

import logging

from ctree import _TYPE_CODEGENERATORS as generators
from ctree import _TYPE_RECOGNIZERS    as recognizers

log = logging.getLogger(__name__)

def register_type_codegenerators(codegen_dict):
    """
    Registers routines for generating code for types.

    :param codegen_dict: Maps type classes to functions that
    take an instance of that class and return the corresponding
    string.
    """
    existing_keys = generators.viewkeys()
    new_keys      = codegen_dict.viewkeys()
    intersection = existing_keys & new_keys
    if intersection:
        log.warning("replacing existing type_codegenerator for %s", intersection)

    for genfn in generators.itervalues():
        assert callable(genfn), "Found a non-callable type_codegen: %s" % genfn

    generators.update(codegen_dict)


def register_type_recognizers(typerec_dict):
    """
    Registers routines for getting ctypes objects from Python objects.

    :param typerec_dict: Maps Python classes to functions that
    take an instance of that class and return the corresponding
    ctypes object.
    """
    existing_keys = recognizers.viewkeys()
    new_keys      = typerec_dict.viewkeys()
    intersection = existing_keys & new_keys
    if intersection:
        log.warning("replacing existing type_recognizer for %s", intersection)

    for genfn in recognizers.itervalues():
        assert callable(genfn), "Found a non-callable type_codegen: %s" % genfn

    recognizers.update(typerec_dict)


def get_ctype(py_obj):
    bases = [type(py_obj)]
    while bases:
        base = bases.pop()
        bases += base.__bases__
        try:
            return recognizers[base](py_obj)
        except KeyError:
            pass
    raise ValueError("No type recognizer defined for %s." % type(py_obj))


def codegen_type(ctype):
    bases = [type(ctype)]
    while bases:
        base = bases.pop()
        bases += base.__bases__
        try:
            val = generators[base](ctype)
            print "MATCH %s (%s) -> %s" % (ctype, base, val)
            return val
        except KeyError:
            pass
    raise ValueError("No code generator defined for %s." % type(ctype))


class c_void(ctypes.c_void_p):
    pass
