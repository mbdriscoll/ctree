Install LLVM 3.4

Clone https://github.com/gentoo90/llvmpy

cd llvmpy

git checkout -b llvm-3.4 origin/llvm-3.4

LLVM_CONFIG_PATH=`which llvm-config-3.4` CC=clang python setup.py install

What could go wrong above?
Does not seem to work on osx when using anaconda base python

Following directions on http://clang-omp.github.io/

git clone https://github.com/clang-omp/llvm
git clone https://github.com/clang-omp/compiler-rt llvm/projects/compiler-rt
git clone -b clang-omp https://github.com/clang-omp/clang llvm/tools/clang


Following seemed to work on Chick's macbook pro
Alternative mac instructions: Using macports with omp support


git clone https://github.com/clang-omp/llvm


sudo LLVM_CONFIG_PATH=llvm-config-mp-3.4 python setup.py install
