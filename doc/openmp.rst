.. openmp:

Using OpenMP with ctree
===================================

``ctree`` can be configured to use `Intel's version of Clang
<http://clang-omp.github.io/>`_ with support for OpenMP.

Dependencies
============

On OSX, ensure that you have the XCode Command Line Tools installed::

        xcode-select --install

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

IMPORTANT: At this point you need to decide where you want to install your llvm.  For this example
We will assume that it will be in /usr/local/llvm_build, for the next step do this from the command
line, via::

        $ export LLVM_BUILD_PATH=/usr/local/llvm_build  # Change this for your particular environment
        $ mkdir $LLVM_BUILD_PATH

Depending on the location of LLVM_BUILD_PATH it may be necessary to use sudo with the mkdir command above, and
in that case you may also want to make that directory owned by someone other than root

Now, build clang/llvm::

        $ mkdir build
        $ cd build
        $ ../llvm/configure --enable-optimized --prefix=$LLVM_BUILD_PATH
        $ REQUIRES_RTTI=1 make
        $ make install

Download and install the Intel OpenMP Runtime Library from
`https://www.openmprtl.org/`, or by installing the
`Intel Compilers
<http://software.intel.com/en-us/intel-compilers>`_.
You can use the evaluation version of the Intel compilers which will install
the OpenMP runtime library.  After 30 days the compilers will cease to work but
the runtime library will still be usable.

Setup your environment variables for a linux system (add this to your .bashrc or .zshrc) in your shell configuration.::
        export LLVM_BUILD_PATH=/usr/local/llvm_build  # Change this for your particular environment
        export OPENMP_RUNTIME_PATH=/usr/local/open_mp # Change this

        export LLVM_BUILD_PATH=/usr/local/llvm-omp
        export OPENMP_RUNTIME_PATH=/opt/intel/composerxe

        export LD_LIBRARY_PATH=/opt/intel/composerxe/lib

        export CPLUS_INCLUDE_PATH=/usr/include/:/usr/include/c++
        export C_INCLUDE_PATH=/usr/include/:/usr/include/c++

        export PATH=$LLVM_BUILD_PATH/bin:$PATH
        export C_INCLUDE_PATH=$LLVM_BUILD_PATH/include:$OPENMP_RUNTIME_PATH/include:$C_INCLUDE_PATH
        export CPLUS_INCLUDE_PATH=$LLVM_BUILD_PATH/include:$OPENMP_RUNTIME_PATH/include:$CPLUS_INCLUDE_PATH
        export LIBRARY_PATH=$LLVM_BUILD_PATH/lib:<OpenMP library path>:$LIBRARY_PATH
        export LD_LIBRARY_PATH=$LLVM_BUILD_PATH/lib:<OpenMP library path>:$LD_LIBRARY_PATH

On Mac OS X, replace LD_LIBRARY_PATH with DYLD_LIBRARY_PATH.::

        export LLVM_BUILD_PATH=/usr/local/llvm_build  # Change this for your particular environment
        export OPENMP_RUNTIME_PATH=/usr/local/open_mp # Change this

        export LLVM_BUILD_PATH=/usr/local/llvm-omp
        export OPENMP_RUNTIME_PATH=/opt/intel/composerxe

        export LD_LIBRARY_PATH=/opt/intel/composerxe/lib

        export CPLUS_INCLUDE_PATH=/usr/include/:/usr/include/c++
        export C_INCLUDE_PATH=/usr/include/:/usr/include/c++

        export PATH=$LLVM_BUILD_PATH/bin:$PATH
        export C_INCLUDE_PATH=$LLVM_BUILD_PATH/include:$OPENMP_RUNTIME_PATH/include:$C_INCLUDE_PATH
        export CPLUS_INCLUDE_PATH=$LLVM_BUILD_PATH/include:$OPENMP_RUNTIME_PATH/include:$CPLUS_INCLUDE_PATH
        export LIBRARY_PATH=$LLVM_BUILD_PATH/lib:<OpenMP library path>:$LIBRARY_PATH
        export LD_LIBRARY_PATH=$LLVM_BUILD_PATH/lib:<OpenMP library path>:$LD_LIBRARY_PATH

        export DYLD_LIBRARY_PATH=/opt/intel/composerxe/lib:$DYLD_LIBRARY_PATH

Download and checkout gentoo90's llvmpy branch with llvm-3.4 support and build
it::

        $ git clone -b llvm-3.4 http://github.com/llvmpy/llvmpy.git
        $ cd llvmpy
        $ LLVM_CONFIG_PATH=YOUR_INSTALL_PATH/bin/llvm-config python setup.py install

Update your ~/.ctree.cfg to use the proper clang and the openmp RTL::

        [omp]
        CC = /Users/your_name/opt/llvm-omp-3.4/bin/clang
        CFLAGS = -march=native -O3 -fopenmp -I/opt/intel/composerxe/include
