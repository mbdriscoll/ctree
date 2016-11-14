"""
OpenMP nodes supported by ctree.
"""

import logging

log = logging.getLogger(__name__)

from ctree.nodes import CtreeNode

# ---------------------------------------------------------------------------
# openmp nodes


class OmpNode(CtreeNode):
    """Base class for all OpenMP nodes supported by ctree."""

    def codegen(self, indent=0):
        from ctree.omp.codegen import OmpCodeGen

        return OmpCodeGen(indent).visit(self)

    def label(self):
        from ctree.omp.dotgen import OmpDotLabeller

        return OmpDotLabeller().visit(self)

    def _requires_semicolon(self):
        return False


class OmpParallel(OmpNode):
    """
    Represents '#pragma omp parallel' annotations.
    """
    _fields = ['clauses']

    def __init__(self, clauses=None):
        self.clauses = clauses if clauses else []


class OmpParallelFor(OmpNode):
    """ #pragma omp parallel for ... """
    _fields = ['clauses']

    def __init__(self, clauses=None):
        self.clauses = clauses if clauses else []


class OmpParallelSections(OmpNode):
    """ #pragma omp parallel sections... """
    _fields = ['clauses', 'sections']

    def __init__(self, clauses=None, sections=None):
        self.clauses = clauses or []
        self.sections = sections or []


class OmpSection(OmpNode):
    """ #pragma omp section ... """
    _fields = ['clauses', 'body']

    def __init__(self, clauses=None, body=None):
        self.clauses = clauses or []
        self.body = body or []


class OmpIvDep(OmpNode):
    _field = ['clauses']

    def __init__(self, clauses=[]):
        self.clauses = clauses


class OmpClause(OmpNode):
    """Base class for OpenMP clauses."""
    pass


class OmpIfClause(OmpClause):
    _fields = ["exp"]

    def __init__(self, exp=None):
        self.exp = exp


class OmpNumThreadsClause(OmpClause):
    _fields = ["val"]

    def __init__(self, val=None):
        self.val = val


class OmpNoWaitClause(OmpClause):
    pass
