from distutils.core import setup

setup(
  name='ctree',
  version='0.95a',
  packages=['ctree',
    'ctree.c',
    'ctree.cilk',
    'ctree.cpp',
    'ctree.ocl',
    'ctree.omp',
    'ctree.py',
    'ctree.sse',
  ],

  package_data = {
    'ctree': ['defaults.cfg'],
  },
)
