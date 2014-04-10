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
        return dedent("""
        // %d lines suppressed, only %d allowed
        // consider adjusting config entry log.max_lines_per_source"""
                      % (n_lines, max_display_lines))


def lower_case_underscore_to_camel_case(string):
    """Convert string or unicode from lower-case underscore to camel-case"""
    # use string's class to work on the string to keep its type
    class_ = string.__class__
    return class_.join('', map(class_.capitalize, string.split('_')))


def highlight(code, language='c'):
    """Syntax-highlight code using pygments, if installed."""
    try:
        from pygments.formatters.terminal256 import Terminal256Formatter
        from pygments.lexers.compiled import CLexer
        from pygments.lexers.asm import LlvmLexer
        from pygments import highlight
    except ImportError:
        log.info("install pygments for syntax-highlighted output.")
        return code

    if   language.lower() == 'llvm': lexer = LlvmLexer()
    elif language.lower() == 'c':    lexer = CLexer()
    else:
        raise ValueError("Unrecognized highlight language: %s" % language)

    style = ctree.CONFIG.get('log', 'pygments_style')
    return highlight(code, lexer, Terminal256Formatter(style=style))
