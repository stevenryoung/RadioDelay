# Sports Radio Delay
# Copyright (C) 2014-2015 Steven Young <stevenryoung@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Python2/3 Compatibility
from __future__ import print_function

if hasattr(__builtins__, "raw_input"):
    input = raw_input

import logging
import logging.config
from multiprocessing import Process, Pipe
import os
from pkg_resources import Requirement, resource_filename
import pyaudio
import argparse


# Initialize Logging
log_settings_file = resource_filename("radiodelay", "radio_delay_log_settings.ini")
logging.config.fileConfig(log_settings_file)
LOG = logging.getLogger("radio_delay")

# Some Global Variables
RD_VERSION = "0.3.0-dev"
DELAY_PROMPT = "Enter your desired delay in seconds. Enter -1 to quit.\n"
COPYRIGHT = (
    "Sports Radio Delay\n"
    "Copyright (C) 2014-2021  Steven Young <stevenryoung@gmail.com>\n"
    "This program comes with ABSOLUTELY NO WARRANTY.\n"
    "This is free software, and you are welcome to redistribute it\n"
    'under certain conditions; type "show details" for more info\n'
)

# Parse Arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "--delay", type=float, help="delay (seconds)", action="store", default=5.0
)
parser.add_argument(
    "--sample_rate", type=int, help="sample rate (hz)", action="store", default=44100
)
parser.add_argument(
    "--chunk", type=int, help="chunk size (bytes)", action="store", default=2048
)
parser.add_argument("--width", type=int, help="width", action="store", default=2)
parser.add_argument(
    "--channels", type=int, help="number of channels", action="store", default=2
)
parser.add_argument(
    "--bffsz",
    type=int,
    help="size of ring buffer (seconds)",
    action="store",
    default=300,
)
parser.add_argument(
    "--primelen",
    type=int,
    help="number of chunks to prime output",
    action="store",
    default=5,
)
ARGS = parser.parse_args()


def write_terminal(desired_delay):
    os.system("cls" if os.name == "nt" else "clear")
    print(COPYRIGHT)
    print("Delay (seconds): {}".format(desired_delay))
    print(DELAY_PROMPT)


def initialize_stream(audio):
    return audio.open(
        format=audio.get_format_from_width(ARGS.width),
        channels=ARGS.channels,
        rate=ARGS.sample_rate,
        input=True,
        output=True,
        frames_per_buffer=ARGS.chunk,
    )


def delay_loop(conn):
    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Initialize Stream
    stream = initialize_stream(p)

    # Establish some parameters
    bps = float(ARGS.sample_rate) / float(ARGS.chunk)  # blocks per second
    desireddelay = ARGS.delay  # delay in seconds
    buffersecs = ARGS.bffsz  # size of buffer in seconds

    # Create buffer
    bfflen = int(buffersecs * bps)
    buff = [0 for x in range(bfflen)]

    # Establish initial buffer pointer
    widx = int(desireddelay * bps)  # pointer to write position
    ridx = 0  # pointer to read position

    # Prewrite empty data to buffer to be read
    blocksize = len(stream.read(ARGS.chunk))
    for tmp in range(bfflen):
        buff[tmp] = "0" * blocksize

    # Write to command prompt
    write_terminal(desireddelay)

    # Preload data into output to avoid stuttering during playback
    for tmp in range(ARGS.primelen):
        stream.write("0" * blocksize, ARGS.chunk)

    # Loop until program terminates
    while True:
        # Read next input
        buff[widx] = stream.read(ARGS.chunk)

        # Write output
        try:
            stream.write(buff[ridx], ARGS.chunk, exception_on_underflow=True)
        except IOError:  # underflow, priming the output
            LOG.warning("Underflow occurred", exc_info=True)
            stream.stop_stream()
            stream.close()
            stream = initialize_stream(p)
            for i in range(ARGS.primelen):
                stream.write("0" * blocksize, ARGS.chunk, exception_on_underflow=False)

        # Update write and read pointers
        widx += 1
        ridx += 1
        if widx == bfflen:
            widx = 0
        if ridx == bfflen:
            ridx = 0

        # Check for updated delay
        if conn.poll():
            desireddelay = conn.recv()
            if desireddelay:
                ridx = int((widx - int(desireddelay * bps)) % bfflen)
                write_terminal(desireddelay)
            else:
                stream.stop_stream()
                stream.close()
                break


def main():
    # Print some info to log
    LOG.info("Radio Delay - {}".format(RD_VERSION))

    # Establish pipe for delay process
    pconn1, cconn1 = Pipe()
    p1 = Process(target=delay_loop, args=(cconn1,))
    p1.start()

    # Loop to check for change in desired delay
    while True:
        inp = input(DELAY_PROMPT)
        try:
            inp = float(inp)
            if inp == -1.0:  # Terminate
                pconn1.send(False)
                break
            elif inp > 0.0:  # Update delay
                pconn1.send(inp)
            else:
                print("Please use a delay longer than 0 sec.")
        except:
            if "show" in inp:  # Give link to license
                print("See the copy of GPLv3 provided with this program")
                print("or <http://www.gnu.org/licenses/> for more details.")
            else:
                print("Improper input.")
    p1.join()


if __name__ == "__main__":
    main()
