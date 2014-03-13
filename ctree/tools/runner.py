"""
create specializer projects
basically copies all files and directories from a template.
"""

import sys
import argparse
from ctree.tools.generators import builder as Builder


__author__ = 'chick'


def main(args):
    parser = argparse.ArgumentParser(prog="ctree", description="ctree is a python SEJITS framework")
    parser.add_argument('-g', '--generate', help='generate a specializer project')
    parser.add_argument('-v', '--verbose', help='show more debug than you like', action="store_true")
    args = parser.parse_args(args)

    if args.generate:
        specializer_name = args.generate

        print "create project specializer %s" % specializer_name

        builder = Builder.Builder("create", specializer_name, verbose=args.verbose)

        builder.build(None, None)
    else:
        parser.print_usage()

if __name__ == '__main__':
    main(sys.argv[1:])
