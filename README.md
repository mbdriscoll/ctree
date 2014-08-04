ctree
=====

A C-family AST implementation designed to be an IR for DSL compilers.

See the [website](http://ucb-sejits.github.io/ctree/) or [documentation](https://ucb-sejits.github.com/ctree-docs/index.html).

[![Build Status](https://travis-ci.org/ucb-sejits/ctree.png?branch=master)](https://travis-ci.org/ucb-sejits/ctree)
[![Coverage Status](https://coveralls.io/repos/ucb-sejits/ctree/badge.png)](https://coveralls.io/r/ucb-sejits/ctree)

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

pip install git+https://github.com/ucb-sejits/ctree
```
