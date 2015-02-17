import logging

log = logging.getLogger(__name__)

from textwrap import dedent

import ctree
import time


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
        return dedent("""
        // %d lines suppressed, only %d allowed
        // consider adjusting config entry log.max_lines_per_source"""
                      % (n_lines, max_display_lines))


def lower_case_underscore_to_camel_case(string):
    """Convert string or unicode from lower-case underscore to camel-case"""
    # use string's class to work on the string to keep its type
    class_ = string.__class__
    return class_.join('', map(class_.capitalize, string.split('_')))


def flatten(obj):
    """Iterator for all objects arbitrarily nested in lists."""
    if isinstance(obj, (set, list)):
        for gen in map(flatten, obj):
            for elem in gen:
                yield elem
    elif isinstance(obj, (dict)):
        for gen in map(flatten, obj.itervalues()):
            for elem in gen:
                yield elem
    else:
        yield obj


def enumerate_flatten(obj_or_list):
    """Iterator for all objects arbitrarily nested in lists."""
    if isinstance(obj_or_list, list):
        for n, gen in enumerate(map(enumerate_flatten, obj_or_list)):
            for k, elem in gen:
                yield (n,)+k, elem
    else:
        yield (), obj_or_list


def highlight(code, language='c'):
    """Syntax-highlight code using pygments, if installed."""
    try:
        from pygments.formatters.terminal256 import Terminal256Formatter
        from pygments import highlight
    except ImportError:
        log.info("install pygments for syntax-highlighted output.")
        return code

    if language.lower() == 'llvm':
        from pygments.lexers.asm import LlvmLexer as TheLexer
    elif language.lower() == 'c':
        from pygments.lexers.compiled import CLexer as TheLexer
    elif language.lower() == 'diff':
        from pygments.lexers.text import DiffLexer as TheLexer
    elif language.lower() == 'ini':
        from pygments.lexers.text import IniLexer as TheLexer
    else:
        raise ValueError("Unrecognized highlight language: %s" % language)

    style = ctree.CONFIG.get('log', 'pygments_style')
    return highlight(code, TheLexer(), Terminal256Formatter(style=style))


class Timer:  # pragma: no cover
    def __enter__(self):
        self.start = time.clock()
        return self

    def __exit__(self, *args):
        self.interval = time.clock() - self.start
