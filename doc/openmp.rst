.. openmp:

Using OpenMP with ctree
===================================

``ctree`` can be configured to use `Intel's version of Clang
<http://clang-omp.github.io/>`_ with support for OpenMP.

Installing OpenMP/Clang
------------------

These instructions are a combination of instructions found from
`http://clang-omp.github.io/`,
`http://llvm.org/docs/GettingStarted.html`
and `https://www.openmprtl.org/`.

First, get the source code::

        $ git clone https://github.com/clang-omp/llvm
        $ git clone https://github.com/clang-omp/compiler-rt llvm/projects/compiler-rt
        $ git clone -b clang-omp https://github.com/clang-omp/clang llvm/tools/clang

Now, build clang/llvm::

        $ mkdir build
        $ cd build
        $ ../llvm/configure --enable-optimized --prefix=YOUR_INSTALL_PATH # i.e. /opt/llvm-omp
        $ REQUIRES_RTTI=1 make
        $ make install

Setup your environment variables (add this to your .bashrc or .zshrc) in your shell configuration. On Mac OS X,
replace LD_LIBRARY_PATH with DYLD_LIBRARY_PATH.::

        PATH=/install/prefix/bin:$PATH
        C_INCLUDE_PATH=/install/prefix/include:<OpenMP include path>:$C_INCLUDE_PATH
        CPLUS_INCLUDE_PATH=/install/prefix/include:<OpenMP include path>:$CPLUS_INCLUDE_PATH
        LIBRARY_PATH=/install/prefix/lib:<OpenMP library path>:$LIBRARY_PATH
        LD_LIBRARY_PATH=/install/prefix/lib:<OpenMP library path>:$LD_LIBRARY_PATH

Download and install the Intel OpenMP Runtime Library from
`https://www.openmprtl.org/`, or by installing the
`Intel Compilers
<http://software.intel.com/en-us/intel-compilershttp://software.intel.com/en-us/intel-compilers>`_.
You can use the evaluation version of the Intel compilers which will install
the OpenMP runtime library.  After 30 days the compilers will cease to work but
the runtime library will still be usable.

Include the OpenMP RTL, for OSX with the evaluation Intel Compilers you can do::

        DYLD_LIBRARY_PATH=/opt/intel/composerxe/lib:$DYLD_LIBRARY_PATH

Download and checkout gentoo90's llvmpy branch with llvm-3.4 support and build
it::

        $ git clone -b llvm-3.4 https://github.com/gentoo90/llvmpy.git
        $ cd llvmpy
        $ LLVM_CONFIG_PATH=YOUR_INSTALL_PATH/bin/llvm-config python setup.py install

Update your ~/.ctree.cfg to use the proper clang and the openmp RTL::

        [jit]
        CC = /Users/your_name/opt/llvm-omp-3.4/bin/clang
        CFLAGS = -march=native -O3 -fopenmp -I/opt/intel/composerxe/include
