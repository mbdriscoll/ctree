"""
ctree extensions for OpenCL.
"""

import logging

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# load OpenCL runtime into memory so it can be used from LLVM's jit

try:
    import ctypes
    import ctypes.util

    libOpenCL = ctypes.util.find_library("OpenCL")
    log.info("loading libOpenCL from %s", libOpenCL)

    import llvm.core

    llvm.core.load_library_permanently(libOpenCL)

except:
    log.warn("Failed to load OpenCL runtime.")
