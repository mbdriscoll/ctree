"""
The ctree package


"""
from __future__ import print_function



# ---------------------------------------------------------------------------
# explicit version check

import sys
# assert sys.version_info[0] >= 3, "ctree requires Python 3.x"
assert sys.version_info[0] >= 2, "ctree requires Python 2.7.x"


# ---------------------------------------------------------------------------
# logging

import logging

LOG = logging.getLogger(__name__)
LOG.info("initializing ctree")

# ---------------------------------------------------------------------------
# configuration file parsing

# pylint disable=import-error
try:
    # python 2
    import ConfigParser as configparser
except ImportError:
    # python 3
    import configparser
# pylint enable=import-error

from os import path, getcwd

CONFIG = configparser.ConfigParser()
DEFAULT_CFG_FILE_PATH = path.join(path.abspath(path.dirname(__file__)), "defaults.cfg")
LOG.info("reading default configuration from: %s", DEFAULT_CFG_FILE_PATH)

CONFIG.readfp(open(DEFAULT_CFG_FILE_PATH), filename="defaults.cfg")

CFG_PATHS = [
    path.expanduser('~/.ctree.cfg'),
    path.join(getcwd(), ".ctree.cfg"),
]
LOG.info("checking for config files at: %s", CFG_PATHS)

LOG.info("found config files: %s", CONFIG.read(CFG_PATHS))

if sys.version_info.major == 2:
    from io import BytesIO as Memfile
else:
    from io import StringIO as Memfile

from ctree.util import highlight

CONFIGFILE = Memfile()
CONFIG.write(CONFIGFILE)
CONFIG_TXT = CONFIGFILE.getvalue()
LOG.info("using configuration:\n%s", highlight(CONFIG_TXT, language='ini'))
CONFIGFILE.close()
if CONFIG.has_option('log','level'):
    logging.basicConfig(level=getattr(logging,CONFIG.get('log','level')))


# ---------------------------------------------------------------------------
# stats

import atexit
import collections


class LogInfo(object):
    """Tracks events, reports counts upon garbage collections."""

    def __init__(self):
        self._counter = collections.Counter()

    def log(self, event_str):
        """record a single named event"""
        self._counter[event_str] += 1

    def report(self):
        """send a counter report of all named events to the log"""
        key_values_string = ""
        for key_value in self._counter.items():
            key_values_string += "  %s: %s\n" % key_value
        LOG.info("execution statistics: (((\n%s)))", key_values_string)


STATS = LogInfo()
atexit.register(STATS.report)

#----------------------------------------------------------------------------
#Temporary directory stuff
import tempfile
import shutil

if CONFIG.getboolean('jit', 'CACHE'):
    STATS.log("recognized that caching is enabled")
else:
    STATS.log("recognized that caching is disabled")

if not CONFIG.getboolean('jit', 'CACHE'):
    compile_path_old = CONFIG.get('jit', 'COMPILE_PATH')
    temporary_path = tempfile.mkdtemp()
    CONFIG.set('jit', 'COMPILE_PATH', temporary_path)

    def reset():
        CONFIG.set('jit', 'COMPILE_PATH', compile_path_old)
        shutil.rmtree(temporary_path)

    atexit.register(reset)

# Registries for type-based logic in extension packages.
_TYPE_CODEGENERATORS = {}
_TYPE_RECOGNIZERS = {}

import ast
import inspect
import ctree.frontend
from ctree.visual.dot_manager import DotManager


def get_ast(func):
    """convenience method for displaying a callable objects ast"""
    return ctree.frontend.get_ast(func)


def ipython_show_ast(tree):
    """
    convenience method to display an AST in ipython
    converts tree in place to a dot format
    then renders that into a png file
    """
    import ctree.dotgen
    return DotManager.dot_ast_to_image(tree)


def browser_show_ast(tree, file_name=None):
    """
    convenience method to display an AST in ipython
    converts tree in place to a dot format
    then renders that into a png file
    """
    import ctree.dotgen
    return DotManager.dot_ast_to_browser(tree, file_name)
