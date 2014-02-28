# ---------------------------------------------------------------------------
# explicit version check

import sys
assert sys.version_info[0] >= 3, "ctree requires Python 3.x"


# ---------------------------------------------------------------------------
# logging

import logging
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# configuration file parsing

import configparser
from os import path, getcwd

config = configparser.ConfigParser()
default_cfg_file_path = path.join(path.abspath( path.dirname(__file__) ), "defaults.cfg")
log.info("reading default configuration from: %s" % default_cfg_file_path)

config.read_file(open(default_cfg_file_path), source="defaults.cfg")

cfg_paths = [
  path.expanduser('~/.ctree.cfg'),
  path.join(getcwd(), ".ctree.cfg"),
]
log.info("checking for config files at: %s" % cfg_paths)

found = config.read(cfg_paths)
log.info("found config files: %s" % found)

# FIXME print out configuration
log.info("using configuration: (FIXME) %s" % config)


# ---------------------------------------------------------------------------
# stats

import atexit
import collections

class Counter(object):
  """Tracks events, reports counts upon garbage collections."""
  def __init__(self):
    self._counter = collections.Counter()

  def log(self, event_str):
    self._counter[event_str] += 1

  def report(self):
    kvs = ""
    for kv in self._counter.items():
      kvs += "  %s: %s\n" % kv
    log.info("execution statistics: <<<\n%s>>>" % kvs)


stats = Counter()
atexit.register(stats.report)
