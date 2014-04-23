#from distutils.core import setup
from setuptools import setup


def make_data_file_list(target, source):
    """
    creates a list of tuples (target_directory, file_list)
    that setup should copy into the egg in
    the install process.  Gets around no way to specify a recursive
    directory tree copy, directories must be created by
    name on left side of tuple against an empty file list on the right
    """
    import os

    def visit(destination_directory, source_directory):
        # print destination_directory + " " + source_directory
        files = os.listdir(source_directory)
        transfer_list = []
        todo = []
        for file_name in files:
            # print type(file_name)
            source_file = os.path.join(source_directory, file_name)
            # print "source_file " + source_file
            next_destination_directory = os.path.join(destination_directory, file_name)

            if file_name.startswith("__") and file_name != '__init__.py':
                pass
            elif os.path.isdir(source_file):
                transfer_list.append((next_destination_directory, []))
                todo.append((next_destination_directory, source_file))
            elif os.path.isfile(source_file):
                transfer_list.append((destination_directory, [source_file]))

        for next_target, next_source in todo:
            transfer_list += visit(next_target, next_source)

        return transfer_list

    return visit(target, source)

data_file_list = make_data_file_list("ctree/tools/generators/templates", "ctree/tools/generators/templates")
# import pprint
# pprint.pprint(data_file_list)


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
        'ctree.np',
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
        'mako',
        'pyserial',
        # 'readline',
    ],

    data_files=data_file_list,

    entry_points={
        'console_scripts': ['ctree = ctree.tools.runner:main'],
    }
)
