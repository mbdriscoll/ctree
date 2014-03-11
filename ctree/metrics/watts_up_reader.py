from __future__ import print_function
"""
Reader that can sample data from a WattsUpMeter: https://www.wattsupmeters.com
API documents are here: https://www.wattsupmeters.com/secure/downloads/CommunicationsProtocol090824.pdf
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

    def __init__(self, port, interval=1000):
        self.serial_port = serial.Serial(port, 115200)
        # initialize lists for keeping data
        self.last_time = time.time()
        self.t = []
        self.interval = interval
        self.power = []
        self.potential = []
        self.current = []
        self.serial_port.write(chr(0x18))

    def set_mode(self, runmode):
        """
        TODO: Fix this, ported from https://github.com/kjordahl/Watts-Up--logger
        See API url above

        """
        self.serial_port.write('#L,W,3,%s,,%d;' % (runmode, self.interval) )
        if runmode == WattsUpReader.INTERNAL_MODE:
            self.serial_port.write('#O,W,1,%d' % WattsUpReader.FULLHANDLING)

    def fetch(self):
        """read one data point from meter"""

        rfds, wfds, efds = select.select( [self.serial_port], [], [], 0.3)
        if rfds:
            device_output = self.serial_port.readline()
            # device_output = self.serial_port.readline()..decode("utf-8")  #python3
            print(device_output)
            if device_output.startswith("#d"):
                fields = device_output.split(',')
                for index, field in enumerate(fields):
                    print("%02d %s" % (index, field))
                watts = float(fields[3]) / 10
                volts = float(fields[4]) / 10
                milliamps = float(fields[5]) / 1000
                watt_hours = float(fields[6]) / 10
                return WattsUpReader.Result(time.time(), watts, watt_hours, volts, milliamps)
        return WattsUpReader.Result(time.time(), 0.0, 0.0, 0.0, 0.0)

    def multi_fetch(self):
        while(True):
            result = self.fetch()
            print(result)
            if result.volts == 0.0:
                return

    def interactive_mode(self):
        while(True):
            print("Prompt", end="")
            user_input = sys.stdin.readline()
            print("got input %s" % user_input)
            if user_input.startswith('q') or user_input.startswith('Q'):
                return
            if user_input:
                print("sending...")
                self.serial_port.write(user_input)
            result = self.multi_fetch()
            print(result)



    def stop(self):
        self.serial_port.close()


if __name__ == "__main__":
    import sys
    # default port name is based on right hand side usb on macbookpro
    usb_port_name = "/dev/tty.usbserial-A600KI7M" if len(sys.argv) < 2 else sys.argv[1]
    watt_reader = WattsUpReader(usb_port_name)

    watt_reader.interactive_mode()

    # watt_reader.set_mode('E')
    # for i in range(4):
    #     result = watt_reader.fetch()
    #     print(result)
    #     time.sleep(5)

    watt_reader.stop()
