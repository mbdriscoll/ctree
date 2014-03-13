"""
create specializer projects
basically copies all files and directories from a template.
"""

import sys
from tools.generators import builder as Builder

__author__ = 'chick'


def create(*args):
    specializer_name = args[0]

    print "create project specializer %s" % specializer_name

    builder = Builder.Builder("create", specializer_name, verbose=True)

    builder.build(None, None)


if __name__ == '__main__':
    create(*sys.argv[1:])
