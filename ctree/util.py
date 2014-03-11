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

class DotManager(object):
    """
    take ast and return an ipython image file
    """

    @staticmethod
    def dot_ast_to_image(ast_node):
        import io
        from IPython.display import Image

        from  ctree.dotgen import to_dot

        dot_text = to_dot(ast_node)

        return DotManager.dot_text_to_image(dot_text)

    @staticmethod
    def dot_text_to_image(text):
        from IPython.display import Image

        dot_output = DotManager.run_dot(text)
        return Image(dot_output, embed=True)

    @staticmethod
    def run_dot(code, options=None, output_format='png'):
        # mostly copied from sphinx.ext.graphviz.render_dot
        import os
        from subprocess import Popen, PIPE
        from sphinx.util.osutil import EPIPE, EINVAL

        if not options:
            options = []
        dot_args = ['dot'] + options + ['-T', output_format]
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

import serial
import time
import select
import collections


class WattsUpReader(object):
    EXTERNAL_MODE = "E"
    INTERNAL_MODE = "I"
    FULL_HANDLING = 2

    Result = collections.namedtuple("Result", ['time', 'watts', 'volts', 'milliamps'])

    def __init__(self, port, interval=1000):
        self.serial_port = serial.Serial(port, 115200)
        # initialize lists for keeping data
        self.last_time = time.time()
        self.t = []
        self.interval = interval
        self.power = []
        self.potential = []
        self.current = []

    def set_mode(self, runmode):
        """
        TODO: Fix this, ported from https://github.com/kjordahl/Watts-Up--logger
        API Notes at
        https://www.wattsupmeters.com/secure/downloads/CommunicationsProtocol090824.pdf
        """
        self.serial_port.write('#L,W,3,%s,,%d;' % (runmode, self.interval) )
        if runmode == WattsUpReader.INTERNAL_MODE:
            self.serial_port.write('#O,W,1,%d' % WattsUpReader.FULLHANDLING)

    def fetch(self):
        """read one data point from meter"""

        rfds, wfds, efds = select.select( [self.serial_port], [], [], 1)
        if rfds:
            device_output = self.serial_port.readline()
            # device_output = self.serial_port.readline()..decode("utf-8")  #python3
            if device_output.startswith("#d"):
                fields = device_output.split(',')
                watts = float(fields[3]) / 10
                volts = float(fields[4]) / 10
                milliamps = float(fields[5]) / 1000
                return WattsUpReader.Result(time.time(), watts, volts, milliamps)
        return WattsUpReader.Result(time.time(), 0.0, 0.0, 0.0)

    def stop(self):
        self.serial_port.close()


if __name__ == "__main__":
    import sys
    # default port name is based on right hand side usb on macbookpro
    usb_port_name = "/dev/tty.usbserial-A600KI7M" if len(sys.argv) < 2 else sys.argv[1]
    watt_reader = WattsUpReader(usb_port_name)

    # watt_reader.set_mode('E')
    for i in range(10):
        tup = watt_reader.fetch()
        print tup
        time.sleep(5)

    watt_reader.stop()
