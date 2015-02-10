"""
create specializer projects
basically copies all files and directories from a template.
"""

import sys
import argparse
import ctree

from ctree.tools.generators import builder as Builder
from subprocess import call as shell



__author__ = 'chick'


def main(*args):
    '''run ctree utility stuff, currently only the project generator'''

    if sys.argv:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="ctree", description="ctree is a python SEJITS framework")
    parser.add_argument('-sp', '--startproject', help='generate a specializer project')
    parser.add_argument(
        '-wu', '--wattsupmeter', help="start interactive watts up meter shell", action="store_true"
    )
    parser.add_argument('-p', '--port', help="/dev name to use for wattsup meter port")
    parser.add_argument('-v', '--verbose', help='show more debug than you like', action="store_true")
    parser.add_argument('-dc', '--disable_cache', help='disable and delete the persistent cache', action="store_true")
    parser.add_argument('-ec', '--enable_cache', help='enable the persistent cache', action="store_true")
    parser.add_argument('-cc', '--clear_cache', help='clear the persistent cache', action="store_true")
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

    elif args.enable_cache:
        ctree.CONFIG.set("jit", "CACHE_ON", value="True")
        write_success = write_to_config()
        if write_success: print("[SUCCESS] ctree caching enabled.")

    elif args.disable_cache:
        ctree.CONFIG.set("jit", "CACHE_ON", value="False")
        write_success = write_to_config()
        clear_cache()
        if write_success: print("[SUCCESS] ctree caching disabled.")

    elif args.clear_cache:
        clear_cache()

    else:
        parser.print_usage()


def write_to_config():
    '''
    This method handles writing to the closest config file to the current
    project, but does not write to the defaults.cfg file in ctree.
    :return: return True if write is successful. False otherwise.
    '''

    if len(ctree.CFG_PATHS) > 0:
        with open(ctree.CFG_PATHS[-1], 'w') as configfile:
            ctree.CONFIG.write(configfile)
            configfile.close()
        return True
    else:
        print("[FAILURE] No config file detected. Please create a '.ctree.cfg' file in your project directory.")
        return False


def clear_cache():
    '''
    This method handles clearing the closest cache to the current project.
    '''
    path = ctree.CONFIG.get("jit", "COMPILE_PATH")
    shell(["rm", "-rf", path])
    print("[SUCCESS] ctree cache deleted from path: " + path)

if __name__ == '__main__':
    main(sys.argv[1:])
