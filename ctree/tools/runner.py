"""
create specializer projects
basically copies all files and directories from a template.
"""

import sys
import argparse
import ctree



import collections
import shutil
import os

from ctree.tools.generators import builder as Builder

if sys.version_info >= (3, 0, 0): #python 3
    import configparser as ConfigParser
else:
    import ConfigParser


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
        ctree.CONFIG.set("jit", "CACHE", value="True")
        write_success = write_to_config('jit', 'CACHE', True)
        if write_success: print("[SUCCESS] ctree caching enabled.")

    elif args.disable_cache:
        wipe_cache()
        ctree.CONFIG.set("jit", "CACHE", value="False")
        write_success = write_to_config('jit', 'CACHE', False)
        args.clear_cache = True
        if write_success: print("[SUCCESS] ctree caching disabled.")

    elif args.clear_cache:
        wipe_cache()

    else:
        parser.print_usage()

def get_responsible(section, key):
    """
    :param section: Section to search for
    :param key: key to search for
    :return: path of config file responsible for setting
    """
    first = ctree.CFG_PATHS[-1]
    paths = reversed(ctree.CFG_PATHS)
    for path in paths:
        config = ConfigParser.ConfigParser()
        config.read(path)
        if config.has_option(section, key):
            return path
    return first

def write_to_config(section, key, value):
    '''
    This method handles writing to the closest config file to the current
    project, but does not write to the defaults.cfg file in ctree.
    :return: return True if write is successful. False otherwise.
    '''

    if ctree.CFG_PATHS:
        target = get_responsible(section, key)
        config = ConfigParser.ConfigParser()
        config.read(target)
        print(target)
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, key, value)
        with open(target, 'w') as configfile:
            config.write(configfile)
            configfile.close()
        return True
    else:
        print("[FAILURE] No config file detected. Please create a '.ctree.cfg' file in your project directory.")
        return False

def wipe_cache():
    cache_name = os.path.expanduser(ctree.CONFIG.get('jit','COMPILE_PATH'))
    if os.path.isabs(cache_name):
        cache_name = os.path.abspath(cache_name)
    else:
        splitted = cache_name.split(os.sep)
        while splitted:
            first = splitted[0]
            if first == '.':
                splitted.pop(0)
            elif first == '..':
                os.chdir('../')
                splitted.pop(0)
            else:
                cache_name = os.sep.join(splitted)
                break

    wipe_queue = collections.deque([os.path.abspath(p) for p in os.listdir(os.getcwd())])
    while wipe_queue:
        directory = wipe_queue.popleft()
        if not os.path.isdir(directory):
            continue
        if os.path.split(directory)[-1] == cache_name:
            shutil.rmtree(directory)
        else:
            for sub_item in os.listdir(directory):
                wipe_queue.append(os.path.join(directory, sub_item))

if __name__ == '__main__':
    main(sys.argv[1:])
