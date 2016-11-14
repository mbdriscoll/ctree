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

    summary, detailed_results = reader.get_recording()
    #
    # summary is a Summary named-tuple
    # detailed_results an array of Result named-tuples defined below
    #

This also is runnable from the command line

python watts_up_reader.py "/dev/tty.usbserial-A600KI7M"

which will put you in an interactive session, that allows testing
of recording, a few other things and direct communication with the
device

the meter is finicky and may not be working if connection is made
quickly after

"""
from __future__ import print_function

__author__ = 'Chick Markley'


import serial
import readline
import time
import select
import collections
import argparse


class WattsUpReader(object):
    EXTERNAL_MODE = "E"
    INTERNAL_MODE = "I"
    FULL_HANDLING = 2

    Result = collections.namedtuple("Result", ['time', 'watts', 'volts', 'milliamps'])
    Response = collections.namedtuple("Response", ['time', 'message'])
    Summary = collections.namedtuple(
        "Summary", ["joules", "millicoulomb", "samples", "sampling_interval", "start_time"]
    )

    def __init__(self, port_name=None, verbose=False):
        if port_name is None:
            from ctree import CONFIG
            port_name = CONFIG.get('wattsup', 'port')
        self.port_name = port_name
        self.serial_port = serial.Serial(self.port_name, 115200)

        self.last_time = time.time()
        self.verbose = verbose
        self.t = []
        self.power = []
        self.returned_lines = 0
        # I don't think device supports anything smaller
        self.record_interval = 1

        self.start_recording()

    def reset(self):
        if self.serial_port:
            self.serial_port.close()
        time.sleep(1)

        self.serial_port = serial.Serial(self.port_name, 115200)
        if self.verbose:
            print("serial port:")
            print(self.serial_port)
        self.serial_port.sendBreak()
        self.serial_port.flushInput()
        self.serial_port.flushOutput()
        self.serial_port.setDTR()
        self.serial_port.write(chr(0x18))
        time.sleep(1)
        self.send_command("#V,W,0;", timeout=10, tries=1)

    def clear(self):
        self.serial_port.write("#R,W,0;")
        self.drain()

    def set_verbose(self, new_value=None):
        if new_value is None:
            self.verbose = not self.verbose
        else:
            self.verbose = new_value

    def set_mode(self, runmode):
        """
        TODO: Fix this, ported from https://github.com/kjordahl/Watts-Up--logger
        See API url above

        """
        self.serial_port.write('#L,W,3,%s,,%d;' % (runmode, self.record_interval))
        if runmode == WattsUpReader.INTERNAL_MODE:
            self.serial_port.write('#O,W,1,%d' % WattsUpReader.FULL_HANDLING)

    def fetch(self, base_time=None, time_out=0.3, raw=False):
        """read one data point from meter"""

        rfds, wfds, efds = select.select([self.serial_port], [], [], time_out)
        if rfds:
            # device_output = self.serial_port.readline()..decode("utf-8")  #python3
            device_output = self.serial_port.readline()
            self.returned_lines += 1
            if self.verbose:
                print(device_output)
            if device_output.startswith("#d"):
                if raw:
                    return "%s,%s" % (device_output.strip(), base_time)

                fields = device_output.split(',')
                if self.verbose:
                    for index, field in enumerate(fields):
                        print("%02d %s" % (index, field))
                watts = float(fields[3]) / 10
                volts = float(fields[4]) / 10
                milliamps = float(fields[5]) / 1000
                if not base_time:
                    base_time = time.time()
                return WattsUpReader.Result(base_time, watts, volts, milliamps)
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

    def dump(self):
        while True:
            result = self.fetch(base_time=time.time(), time_out=1000)
            print(result)

    def raw_dump(self):
        while True:
            result = self.fetch(base_time=time.time(), time_out=1000, raw=True)
            print(result)

    def send_command(self, command, timeout=3, tries=3):
        if not command.startswith("#"):
            print( "Error: no initial # for command %s", command)
            return
        if not command.strip().endswith(";"):
            print( "Error: no trailing ; for command %s", command)
            return

        for tries in range(tries):
            if self.verbose:
                print("sending command %s" % command)
            self.serial_port.write(command)

            answer = self.fetch(time_out=timeout)
            if answer:
                if self.verbose:
                    print("answer %s",end="")
                    print(answer)
                self.last_time = time.time()
                return
            else:
                if self.verbose:
                    print("timed out sending command %s" % command)

    def start_recording(self):
        self.drain()

        command = "#L,W,3,E,,%d;" % self.record_interval
        self.send_command(command)

    def get_recording(self):
        def pull():
            results = []
            estimated_record_time = self.last_time
            watt_seconds = 0.0
            samples = 0
            millicoulombs = 0.0

            while True:
                result = self.fetch(estimated_record_time)
                if not result:
                    summary = WattsUpReader.Summary(
                        watt_seconds, millicoulombs, samples, self.record_interval, self.last_time
                    )
                    return summary, results
                if type(result) is WattsUpReader.Result:
                    results.append(result)
                    watt_seconds += result.watts
                    millicoulombs += result.milliamps
                    samples += 1
                    estimated_record_time += self.record_interval
        all_results = pull()
        self.last_time = time.time()
        return all_results

    def command(self, string):
        self.serial_port.write(string)
        save_verbose, self.verbose = self.verbose, True
        time.sleep(1)
        self.drain()
        self.verbose = save_verbose

    @staticmethod
    def usage():
        print("command must be one of (quit, reset, record, get_record, verbose, drain) or ")
        print("native device command string beginning with # ")
        print("empty command will repeat previous command")
        print("commands can be abbreviated to first three letters")
        print("\n")

    def interactive_mode(self):
        readline.parse_and_bind('tab: complete')
        readline.parse_and_bind('set editing-mode vi')

        last_input = None
        WattsUpReader.usage()
        while True:
            # print("Command: ", end="")
            # user_input = sys.stdin.readline()

            user_input = raw_input("Command (quit to exit): ")
            # print("got input %s" % user_input)
            # if user_input.strip() == '':
            #     user_input = last_input

            if user_input.startswith('q') or user_input.startswith('Q'):
                return
            elif user_input.lower().startswith('res'):
                self.reset()
            elif user_input.lower().startswith('dra'):
                self.drain()
            elif user_input.lower().startswith('rec'):
                self.start_recording()
            elif user_input.lower().startswith('get'):
                summary, detailed_results = self.get_recording()
                for index, result in enumerate(detailed_results):
                    print("%d ----" % index, end='')
                    print(result)
                print(summary)
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
            last_input = user_input

    def stop(self):
        self.serial_port.close()

    @staticmethod
    def guess_port():
        import subprocess

        for tty_search_command in ["ls /dev/tty*usb*","ls /dev/tty*USB*"]:
            try:
                possible_devices = subprocess.check_output(tty_search_command, shell=True).strip().split('\n')
            except:
                possible_devices = []

            if len(possible_devices) == 1:
                return possible_devices[0]
            else:
                for device in possible_devices:
                    print("Possible device %s" % device)
                print("Multiple possible devices found, you must specify explicitly")
                exit(1)

        print("No potential usb based readers found, is it plugged in?")
        exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="interface to WattsUpPro usb power meter")
    parser.add_argument(
        '-i', '--interactive', help='interactive mode, allows direct communcation with device', action="store_true"
    )
    parser.add_argument('-p', '--port', help='full /dev/ path to the usb device, if missing a good quess will be made')
    parser.add_argument('-d', '--dump', help='meter data to stdout, default is prettified', action="store_true")
    parser.add_argument('-r', '--raw', help='modify dump to return raw device output', action="store_true")
    parser.add_argument('-c', '--clear', help='clear any saved lines in device', action="store_true")
    parser.add_argument('-v', '--verbose', help='show more debug than you like', action="store_true")

    args = parser.parse_args()

    if not args.port:
        usb_port_name = WattsUpReader.guess_port()
        print("Using port %s" % usb_port_name)
    else:
        usb_port_name = args.port

    watt_reader = WattsUpReader(usb_port_name, verbose=False)

    if args.verbose:
        watt_reader.set_verbose(True)
    if args.clear:
        watt_reader.drain()

    if args.interactive:
        watt_reader.interactive_mode()
    if args.raw:
        watt_reader.raw_dump()
    elif args.dump:
        watt_reader.dump()
    else:
        parser.print_usage()

    watt_reader.stop()
