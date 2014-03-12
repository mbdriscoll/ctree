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
        print (tup)
        time.sleep(5)

    watt_reader.stop()
