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

CONFIGFILE = Memfile()
CONFIG.write(CONFIGFILE)
CONFIG_TXT = CONFIGFILE.getvalue()
LOG.info("using configuration:\n%s", CONFIG_TXT)
CONFIGFILE.close()


# ---------------------------------------------------------------------------
# stats

import atexit
import collections


class Counter(object):
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


STATS = Counter()
atexit.register(STATS.report)
