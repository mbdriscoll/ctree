__author__ = 'Chick Markley'

import sys
import ast
import math
import time

class Timer(object):
  """
  Context manager for timing sections of code.
  """
  class _stopwatch(object):
    """
    Times a particular key.
    """
    def __init__(self):
      self.x = 0.0
      self.x2 = 0.0
      self.nLaps = 0

    def start(self):
      self._start = time.time()
      self.nLaps += 1

    def lap(self):
       t = time.time() - self._start
       self.x  += t
       self.x2 += t*t

    def mean(self):
      if self.nLaps == 0:
        return 0
      else:
        return self.x / float(self.nLaps)

    def stddev(self):
      if self.nLaps == 0:
        return 0
      else:
        avg = self.mean()
        return math.sqrt(self.x2/float(self.nLaps) - (avg*avg))

    def dict(self):
      return {
        "nTrials": self.nLaps,
        "mean":    self.mean(),
        "stddev":  self.stddev(),
      }

  def __init__(self):
    self.watches = {}

  def __enter__(self):
    self.watches[self._key].start()

  def __exit__(self, type, value, traceback):
    self.watches[self._key].lap()

  def __call__(self, key):
    if key not in self.watches:
      self.watches[key] = Timer._stopwatch()
    self._key = key
    return self

  def dict(self):
    return {k: self.watches[k].dict() for k in self.watches}


class DotManager(object):
    """
    take ast and return an ipython image file
    """
    @staticmethod
    def dot_ast_to_image(ast_node):
        import io
        from IPython.display import Image

        import ctree.dotgen.to_dot
        dot_text = to_dot(ast_node)

        return DotManager.dot_text_to_image(dot_text)

    @staticmethod
    def dot_text_to_image(text):
        from IPython.display import Image

        dot_output = DotManager.run_dot(text)
        return Image(dot_output,embed=True)

    @staticmethod
    def run_dot(code, options=[], format='png'):
        # mostly copied from sphinx.ext.graphviz.render_dot
        import os
        from subprocess import Popen, PIPE
        from sphinx.util.osutil import EPIPE, EINVAL

        dot_args = ['dot'] + options + ['-T', format]
        if os.name == 'nt':
            # Avoid opening shell window.
            # * https://github.com/tkf/ipython-hierarchymagic/issues/1
            # * http://stackoverflow.com/a/2935727/727827
            p = Popen(dot_args, stdout=PIPE, stdin=PIPE, stderr=PIPE,
                      creationflags=0x08000000)
        else:
            p = Popen(dot_args, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        went_wrong = False
        try:
            # Graphviz may close standard input when an error occurs,
            # resulting in a broken pipe on communicate()
            stdout, stderr = p.communicate(code.encode('utf-8'))
        except (OSError, IOError) as err:
            if err.errno != EPIPE:
                raise
            went_wrong = True
        except IOError as err:
            if err.errno != EINVAL:
                raise
            went_wrong = True
        if went_wrong:
            # in this case, read the standard output and standard error streams
            # directly, to get the error message(s)
            stdout, stderr = p.stdout.read(), p.stderr.read()
            p.wait()
        if p.returncode != 0:
            raise RuntimeError('dot exited with error:\n[stderr]\n{0}'
                               .format(stderr.decode('utf-8')))
        return stdout
