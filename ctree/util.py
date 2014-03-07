__author__ = 'Chick Markley'

from textwrap import dedent

import ctree

def singleton(cls):
    instance = cls()
    instance.__call__ = lambda: instance
    return instance

def truncate(text):
    max_display_lines = ctree.CONFIG.getint("log", "max_lines_per_source")
    n_lines = len(text.splitlines())
    if n_lines <= max_display_lines:
        return text
    else:
        return dedent("""\
        // %d lines suppressed, only %d allowed
        // consider adjusting config entry log.max_lines_per_source""" \
        % (n_lines, max_display_lines))
