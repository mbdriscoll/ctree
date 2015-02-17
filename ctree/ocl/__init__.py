"""
ctree extensions for OpenCL.
"""

import logging

log = logging.getLogger(__name__)


import pycl

from ctree.types import (
    codegen_type,
    register_type_recognizers,
    register_type_codegenerators,
)

register_type_recognizers({
})

register_type_codegenerators({
    pycl.cl_context:        lambda t: "cl_context",
    pycl.cl_command_queue:  lambda t: "cl_command_queue",
    pycl.cl_kernel:         lambda t: "cl_kernel",
    pycl.cl_mem:            lambda t: "cl_mem",
})


devices_context_queue_map = {}


def get_context_and_queue_from_devices(devices):
    key = tuple(device.vendor_id for device in devices)
    try:
        return devices_context_queue_map[key]
    except KeyError:
        context = pycl.clCreateContext(devices)
        queue = pycl.clCreateCommandQueue(context)
        devices_context_queue_map[key] = (context, queue)
        return devices_context_queue_map[key]
