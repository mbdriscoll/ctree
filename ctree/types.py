from __future__ import absolute_import

import types
import sys

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
        bases += base.__bases__
        try:
            val = generators[base](ctype)
            return val
        except KeyError:
            pass
    raise ValueError("No code generator defined for %s." % type(ctype))
