from __future__ import annotations
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

import logging
import logging.config
from multiprocessing import Process, Pipe
import os
import importlib.resources
import pyaudio
import argparse


# Initialize Logging
log_settings_file = importlib.resources.files("radiodelay").joinpath(
                    "radio_delay_log_settings.ini")
logging.config.fileConfig(log_settings_file)
LOG = logging.getLogger('radio_delay')

# Some Global Variables
RD_VERSION = '0.3.0'
DELAY_PROMPT = 'Enter your desired delay in seconds. Enter -1 to quit.\n'
COPYRIGHT = ('Sports Radio Delay\n'
             'Copyright (C) 2014-2015  Steven Young <stevenryoung@gmail.com>\n'
             'This program comes with ABSOLUTELY NO WARRANTY.\n'
             'This is free software, and you are welcome to redistribute it\n'
             'under certain conditions; type "show details" for more info\n')

# Parse Arguments
parser = argparse.ArgumentParser()
parser.add_argument('--delay', type=float, help='delay (seconds)', 
                    action='store', default=5.0)
parser.add_argument('--sample_rate', type=int, help='sample rate (hz)',
                    action='store', default=44100)
parser.add_argument('--chunk', type=int, help='chunk size (bytes)',
                    action='store', default=4096)
parser.add_argument('--width', type=int, help='width',
                    action='store', default=2)
parser.add_argument('--channels', type=int, help='number of channels',
                    action='store', default=2)
parser.add_argument('--bffsz', type=int, help='size of ring buffer (seconds)',
                    action='store', default=300)
parser.add_argument('--primelen', type=int, help='number of chunks to prime output',
                    action='store', default=5)
parser.add_argument('--list-devices', help='List available audio devices',
                    action='store_true')
parser.add_argument('--input', help='Device ID for input (see --list-devices')
parser.add_argument('--output', help='Device ID for output (see --list-devices')
ARGS = parser.parse_args()


def write_terminal(desired_delay) -> None:
    """Redraw main control screen"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(COPYRIGHT)
    print("Delay (seconds): {}".format(desired_delay))
    print(DELAY_PROMPT)


def initialize_stream(audio):
    """Activate a PyAudio device"""
    # Use input/output devices if specified, else revert to default
    input_device = ARGS.input
    if not input_device:
        input_device = audio.get_default_host_api_info().get('defaultInputDevice')
    LOG.debug('Set input device to {}'.format(input_device))

    output_device = ARGS.output
    if not output_device:
        output_device = audio.get_default_host_api_info().get('defaultOutputDevice')
    LOG.debug('Set output device to {}'.format(input_device))

    return audio.open(format=audio.get_format_from_width(ARGS.width),
                    channels=ARGS.channels,
                    rate=ARGS.sample_rate,
                    input=True,
                    input_device_index=int(input_device),
                    output=True,
                    output_device_index=int(output_device),
                    frames_per_buffer=ARGS.chunk)


def delay_loop(conn) -> None:
    """Parallel process to handle audio buffering"""
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
    blocksize = len(stream.read(ARGS.chunk, exception_on_overflow=False))
    for tmp in range(bfflen):
        buff[tmp] = '0' * blocksize

    # Write to command prompt
    write_terminal(desireddelay)

    # Preload data into output to avoid stuttering during playback
    for tmp in range(ARGS.primelen):
        stream.write('0' * blocksize, ARGS.chunk)

    # Loop until program terminates
    while True:
        # Read next input
        buff[widx] = stream.read(ARGS.chunk, exception_on_overflow=False)

        # Write output
        stream.write(buff[ridx], ARGS.chunk)

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


def list_devices() -> None:
    p = pyaudio.PyAudio()
    default_api = p.get_default_host_api_info().get('index')
    info = p.get_host_api_info_by_index(default_api)

    print('\nAvailable devices:\n\n'
          'ID#  Input   Output  Name\n'
          '---  ------  ------  ----------------')
    for i in range(0, info.get('deviceCount')):
        device = p.get_device_info_by_host_api_device_index(default_api, i)
        is_input = device.get('maxInputChannels') > 0
        is_output = device.get('maxOutputChannels') > 0
        if is_input or is_output:
            print(f'{i:<3}  {is_input!s:6}  {is_output!s:6}  {device["name"]}')
    print('\nUse --input and --output with the ID# to specify a device\n')


def main() -> None:
    # Print some info to log
    LOG.info('Radio Delay - {}'.format(RD_VERSION))

    # If listing devices, don't start the normal loop
    if ARGS.list_devices:
        list_devices()
        return

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
                print('Please use a delay longer than 0 sec.')
        except ValueError:
            if 'show' in inp:  # Give link to license
                print('See the copy of GPLv3 provided with this program')
                print('or <http://www.gnu.org/licenses/> for more details.')
            else:
                print('Improper input.')
    p1.join()


if __name__ == '__main__':
    main()
