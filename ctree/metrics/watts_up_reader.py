from __future__ import print_function
"""
Reader that can sample data from a WattsUpMeter: https://www.wattsupmeters.com
API documents are here: https://www.wattsupmeters.com/secure/downloads/CommunicationsProtocol090824.pdf

basic usage is as follows

    reader = WattsUpReader("/dev/tty.usbserial-A600KI7M")
    reader.drain()

    reader.start_recording()

    #
    # do a bunch of stuff that uses power
    #

    results = reader.stop_recording()
    #
    # results is an array of Result named-tuples defined below
    #

This also is runnable from the command line

python watts_up_reader.py "/dev/tty.usbserial-A600KI7M"

which will put you in an interactive session, that allows testing
of recording, a few other things and direct communication with the
device


"""
__author__ = 'Chick Markley'


import serial
import time
import select
import collections


class WattsUpReader(object):
    EXTERNAL_MODE = "E"
    INTERNAL_MODE = "I"
    FULL_HANDLING = 2

    Result = collections.namedtuple("Result", ['time', 'watts', 'watthours', 'volts', 'milliamps'])
    Response = collections.namedtuple("Response", ['time', 'message'])

    def __init__(self, port_name, verbose=False):
        self.port_name = port_name
        self.serial_port = serial.Serial(self.port_name, 115200)

        self.last_time = time.time()
        self.verbose = verbose
        self.t = []
        self.power = []
        self.potential = []
        self.current = []
        self.serial_port.write(chr(0x18))
        self.returned_lines = 0
        # I don't think device support anything smaller
        self.record_interval = 1

    def reset(self):
        if self.serial_port:
            self.serial_port.close()

        self.serial_port = serial.Serial(self.port_name, 115200)
        self.serial_port.write(chr(0x18))
        self.serial_port.write("#R,W,0;")

    def clear(self):
        self.serial_port.write("#R,W,0;")
        self.drain()

    def set_mode(self, runmode):
        """
        TODO: Fix this, ported from https://github.com/kjordahl/Watts-Up--logger
        See API url above

        """
        self.serial_port.write('#L,W,3,%s,,%d;' % (runmode, self.record_interval) )
        if runmode == WattsUpReader.INTERNAL_MODE:
            self.serial_port.write('#O,W,1,%d' % WattsUpReader.FULLHANDLING)

    def fetch(self, base_time=None):
        """read one data point from meter"""

        rfds, wfds, efds = select.select( [self.serial_port], [], [], 0.3)
        if rfds:
            # device_output = self.serial_port.readline()..decode("utf-8")  #python3
            device_output = self.serial_port.readline()
            self.returned_lines += 1
            if self.verbose:
                print(device_output)
            if device_output.startswith("#d"):
                fields = device_output.split(',')
                if self.verbose:
                    for index, field in enumerate(fields):
                        print("%02d %s" % (index, field))
                watts = float(fields[3]) / 10
                volts = float(fields[4]) / 10
                milliamps = float(fields[5]) / 1000
                watt_hours = float(fields[6]) / 10
                if not base_time:
                    base_time = time.time()
                return WattsUpReader.Result(base_time, watts, watt_hours, volts, milliamps)
            elif len(device_output) > 0:
                return WattsUpReader.Response(time.time(), device_output)
        return None

    def drain(self):
        while True:
            result = self.fetch()
            if type(result) is WattsUpReader.Response:
                print(result)
            elif self.verbose:
                print(result)
            if not result:
                return

    def start_recording(self):
        self.drain()
        self.serial_port.write("#L,W,3,I,0,%d" % self.record_interval)
        self.last_time = time.time()

    def done_recording(self):
        def pull():
            results = []
            estimated_record_time = self.last_time
            while True:
                result = self.fetch(estimated_record_time)
                if not result:
                    return results
                if type(result) is WattsUpReader.Result:
                    results.append(result)
                    estimated_record_time += self.record_interval
        all_results = pull()
        return all_results

    @staticmethod
    def usage():
        print(" must be one of (quit, reset, record, done, verbose, drain) or ")
        print("native device command string beginning with # ")
        print("empty command will repeat previous command")

    def interactive_mode(self):
        last_input = None
        WattsUpReader.usage()
        while True:
            print("Command: ", end="")
            user_input = sys.stdin.readline()
            # print("got input %s" % user_input)
            if user_input == '':
                user_input = last_input

            if user_input.startswith('q') or user_input.startswith('Q'):
                return
            elif user_input.lower().startswith('res'):
                self.reset()
            elif user_input.lower().startswith('dra'):
                self.drain()
            elif user_input.lower().startswith('rec'):
                self.start_recording()
            elif user_input.lower().startswith('don'):
                results = self.done_recording()
                for index, result in enumerate(results):
                    print("%d ----" % index, end='')
                    print(result)
            elif user_input.lower().startswith('ver'):
                self.verbose = not self.verbose
            elif user_input.startswith("#"):
                print("sending...")
                self.serial_port.write(user_input)
                time.sleep(1)
                self.drain()
            else:
                print("unknown command: %s" % user_input)
                WattsUpReader.usage()

    def stop(self):
        self.serial_port.close()


if __name__ == "__main__":
    import sys
    # default port name is based on right hand side usb on macbookpro
    usb_port_name = "/dev/tty.usbserial-A600KI7M" if len(sys.argv) < 2 else sys.argv[1]
    watt_reader = WattsUpReader(usb_port_name, verbose=False)

    watt_reader.interactive_mode()

    # watt_reader.set_mode('E')
    # for i in range(4):
    #     result = watt_reader.fetch()
    #     print(result)
    #     time.sleep(5)

    watt_reader.stop()
