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

import gflags
from gflags import FLAGS
import logging
import logging.config
from multiprocessing import Process, Pipe
import os
from pkg_resources import Requirement, resource_filename
import pyaudio
import sys

# Initialize Logging
filename = resource_filename('radiodelay','radio_delay_log_settings.ini') 
print filename
logging.config.fileConfig(filename)
LOG = logging.getLogger('radio_delay')

# Some Global Variables
RD_VERSION = '0.1.0'
DELAY_PROMPT = 'Enter your desired delay in seconds. Enter -1 to quit.\n'
COPYRIGHT = ('Sports Radio Delay\n'
             'Copyright (C) 2014-2015  Steven Young <stevenryoung@gmail.com>\n'
             'This program comes with ABSOLUTELY NO WARRANTY.\n'
             'This is free software, and you are welcome to redistribute it\n'
             'under certain conditions; type "show details" for more info\n')

# Configurable through command line options
gflags.DEFINE_float('delay', 5.0, 'delay (s)')
gflags.DEFINE_integer('sample_rate', 44100, 'sample rate (hz)')
gflags.DEFINE_integer('chunk', 2048, 'chunk size (bytes)')
gflags.DEFINE_integer('width', 2, 'width')
gflags.DEFINE_integer('channels', 2, 'number of channels')
gflags.DEFINE_integer('bffsz', 300, 'size of ring buffer (seconds)')
gflags.DEFINE_integer('primelen', 5, 'number of chunks to prime output')


def write_terminal(desired_delay):
    os.system('cls' if os.name == 'nt' else 'clear')
    print COPYRIGHT
    print "Delay (seconds):", desired_delay
    print DELAY_PROMPT


def delay_loop(conn):
    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Initialize Stream
    stream = p.open(format=p.get_format_from_width(FLAGS.width),
                    channels=FLAGS.channels,
                    rate=FLAGS.sample_rate,
                    input=True,
                    output=True,
                    frames_per_buffer=FLAGS.chunk)

    # Establish some parameters
    bps = float(FLAGS.sample_rate) / float(FLAGS.chunk)  # blocks per second
    desireddelay = FLAGS.delay  # delay in seconds
    buffersecs = FLAGS.bffsz  # size of buffer in seconds

    # Create buffer
    bfflen = int(buffersecs * bps)
    buff = [0 for x in range(bfflen)]

    # Establish initial buffer pointer
    widx = int(desireddelay * bps)  # pointer to write position
    ridx = 0  # pointer to read position

    # Prewrite empty data to buffer to be read
    blocksize = len(stream.read(FLAGS.chunk))
    for tmp in range(bfflen):
        buff[tmp] = '0' * blocksize

    # Write to command prompt
    write_terminal(desireddelay)

    # Preload data into output to avoid stuttering during playback
    for tmp in range(FLAGS.primelen):
        stream.write('0' * blocksize, FLAGS.chunk)

    # Loop until program terminates
    while True:
        # Read next input
        buff[widx] = stream.read(FLAGS.chunk)

        # Write output
        try:
            stream.write(buff[ridx], FLAGS.chunk, exception_on_underflow=True)
        except IOError:  # underflow, priming the output
            LOG.warning("Underflow occurred", exc_info=True)
            stream.stop_stream()
            stream.close()
            stream = p.open(format=p.get_format_from_width(FLAGS.width),
                            channels=FLAGS.channels,
                            rate=FLAGS.sample_rate,
                            input=True,
                            output=True,
                            frames_per_buffer=FLAGS.chunk)
            for i in range(FLAGS.primelen):
                stream.write('0' * blocksize, FLAGS.chunk, exception_on_underflow=False)

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


def main(argv):
    # Print some info to log
    LOG.info("Radio Delay - {}".format(RD_VERSION))

    # Read flags
    try:
      argv = FLAGS(argv)  # parse flags
    except gflags.FlagsError, e:
      print '%s\\nUsage: %s ARGS\\n%s' % (e, sys.argv[0], FLAGS)
      sys.exit(1)

    # Establish pipe for delay process
    pconn1, cconn1 = Pipe()
    p1 = Process(target=delay_loop, args=(cconn1,))
    p1.start()

    # Loop to check for change in desired delay
    while True:
        inp = raw_input(DELAY_PROMPT)
        try:
            inp = float(inp)
            if inp == -1.0:  # Terminate
                pconn1.send(False)
                break
            elif inp > 0.0:  # Update delay
                pconn1.send(inp)
            else:
                print "Please use a delay longer than 0 sec."
        except:
            if "show" in inp:  # Give link to license
                print "See the copy of GPLv3 provided with this program"
                print "or <http://www.gnu.org/licenses/> for more details."
            else:
                print "Improper input."
    p1.join()


if __name__ == '__main__':
    main(sys.argv)
