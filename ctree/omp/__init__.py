"""
ctree extensions for OpenMP.
"""

import logging

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# load omp runtime into memory so it can be used from LLVM's jit

try:
    import ctypes
    import ctypes.util
    import platform

    libiomp5 = ctypes.util.find_library("iomp5")
    # Hack because python bug for ubuntu?
    if libiomp5 is None:
        arch, os = platform.architecture()
        if arch == '32bit':
            libiomp5 = "/opt/intel/composerxe/lib/ia32/libiomp5.so"
        else:
            libiomp5 = "/opt/intel/composerxe/lib/intel64/libiomp5.so"
    log.info("loading libiomp5 from %s" % libiomp5)

    import llvm.core

    llvm.core.load_library_permanently(libiomp5)

    #iomp_handle = ctypes.cdll.LoadLibrary(libiomp5)
    #iomp_handle.__kmpc_barrier
except:
    log.warn("Failed to load OpenMP runtime.")
