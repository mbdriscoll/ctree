"""
create specializer projects
basically copies all files and directories from a template.
"""

import sys
import argparse
import ctree
from ctree.tools.generators import builder as Builder


__author__ = 'chick'


def main(*args):
    """run ctree utility stuff, currently only the project generator"""

    if sys.argv:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="ctree", description="ctree is a python SEJITS framework")
    parser.add_argument('-sp', '--startproject', help='generate a specializer project')
    parser.add_argument(
        '-wu', '--wattsupmeter', help="start interactive watts up meter shell", action="store_true"
    )
    parser.add_argument('-p', '--port', help="/dev name to use for wattsup meter port")
    parser.add_argument('-v', '--verbose', help='show more debug than you like', action="store_true")
    parser.add_argument('-dc', '--disable_caching', help='disable the persistent caching mechanism', action="store_true")
    parser.add_argument('-ec', '--enable_caching', help='enable the persistent caching mechanism', action="store_true")
    args = parser.parse_args(args)

    if args.startproject:
        specializer_name = args.startproject

        print "create project specializer %s" % specializer_name

        builder = Builder.Builder("create", specializer_name, verbose=args.verbose)
        builder.build(None, None)
        
    elif args.wattsupmeter:
        from ctree.metrics.watts_up_reader import WattsUpReader

        port = args.port if args.port else WattsUpReader.guess_port()
        meter = WattsUpReader(port_name=port)
        meter.interactive_mode()

    elif args.enable_caching:
        ctree.CONFIG.set("jit", "CACHE_ON", value="True")

        with open(ctree.CFG_PATHS[-1], 'w') as configfile:
            ctree.CONFIG.write(configfile)
            configfile.close()

    elif args.disable_caching:
        ctree.CONFIG.set("jit", "CACHE_ON", value="False")

        with open(ctree.CFG_PATHS[-1], 'w') as configfile:
            ctree.CONFIG.write(configfile)
            configfile.close()

    else:
        parser.print_usage()

if __name__ == '__main__':
    main(sys.argv[1:])
