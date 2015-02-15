ctree
=====

A C-family AST implementation designed to be an IR for DSL compilers.

See the [website](http://ucb-sejits.github.io/ctree/) or [documentation](https://ucb-sejits.github.com/ctree-docs/index.html).

[![Build Status](https://travis-ci.org/ucb-sejits/ctree.png?branch=master)](https://travis-ci.org/ucb-sejits/ctree)
[![Coverage Status](https://coveralls.io/repos/ucb-sejits/ctree/badge.png)](https://coveralls.io/r/ucb-sejits/ctree)
[![Documentation Status](https://readthedocs.org/projects/ctree/badge/?version=latest)](https://readthedocs.org/projects/ctree/?badge=latest)

Quick install
-------------
### OSX
This installation will not support use of OpenMP.
```shell
brew tap homebrew/versions
brew install llvm34 --with-clang --rtti
LLVM_CONFIG_PATH=llvm-config-3.4 pip install git+https://github.com/llvmpy/llvmpy.git@llvm-3.4
pip install git+https://github.com/ucb-sejits/pycl

pip install pygments numpy nose sphinx

# For using our DOT viewers
# brew install graphviz

pip install git+https://github.com/ucb-sejits/ctree
```

OpenMP Support
--------------
After following the quick install steps above, run this.
```shell
brew tap ucb-sejits/sejits
brew install --HEAD ucb-sejits/sejits/libomp ucb-sejits/sejits/clang-omp
LLVM_CONFIG_PATH=/usr/local/Cellar/clang-omp/HEAD/bin/llvm-config pip install git+https://github.com/llvmpy/llvmpy.git@llvm-3.4
```
Then, append to your `~/.ctree.cfg`.
```
[omp]
CC = /usr/local/opt/clang-omp/bin/clang
CFLAGS = -march=native -O3 -fopenmp
```

To test, try running the OpenMP specializer example.
```shell
PYTHONPATH=`pwd` python examples/OmpSpecializer.py
```
If all goes well, you should see an output containing
```shell
...
Hello from thread 0 of 4.
Hello from thread 1 of 4.
Hello from thread 3 of 4.
Hello from thread 2 of 4.
Done.
INFO:ctree:execution statistics: (((
  specialized function call: 1
  specialized function cache miss: 1
)))
```
