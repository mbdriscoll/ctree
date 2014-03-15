#from distutils.core import setup
from setuptools import setup

setup(
    name='ctree',
    version='0.95a',

    packages=[
        'ctree',
        'ctree.c',
        'ctree.cilk',
        'ctree.cpp',
        'ctree.ocl',
        'ctree.omp',
        'ctree.py',
        'ctree.simd',
        'ctree.templates',
        'ctree.opentuner',
        'ctree.metrics',
        'ctree.tools',
        'ctree.tools.generators',
        'ctree.visual',
    ],

    package_data={
        'ctree': ['defaults.cfg'],
    },

    install_requires=[
        'numpy',
        'pyserial',
    ],

    entry_points={
        'console_scripts': ['ctree = ctree.tools.runner:main'],
    }
)
