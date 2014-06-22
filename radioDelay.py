# RadioDelay (aka Verne-Be-Gone)
# Copyright (C) 2014 Steven Young <stevenryoung@gmail.com>
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

import pyaudio
from multiprocessing import Process, Pipe
import os
import sys
import time

DELAY_PROMPT = 'Enter your desired delay in seconds. Enter -1 to quit.\n'
SAMPLE_RATE = 44100
CHUNK = 2048
WIDTH = 2

COPYRIGHT = ('RadioDelay (aka Verne-Be-Gone)\n'
             'Copyright (C) 2014  Steven Young <stevenryoung@gmail.com>\n'
             'This program comes with ABSOLUTELY NO WARRANTY.\n'
             'This is free software, and you are welcome to redistribute it\n'
             'under certain conditions; type "show details" for more info\n')

def write_terminal(desireddelay):
    os.system('cls' if os.name == 'nt' else 'clear')
    print COPYRIGHT
    print "Delay (seconds):", desireddelay
    print DELAY_PROMPT
    

def delay_loop(channels=2, filename='default.wav', conn=[]):

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Initialize Stream
    stream = p.open(format=p.get_format_from_width(WIDTH),
                    channels=channels,
                    rate=SAMPLE_RATE,
                    input=True,
                    output=True,
                    frames_per_buffer=CHUNK)

    # Establish some parameters
    bps = float(SAMPLE_RATE)/float(CHUNK) # blocks per second
    desireddelay = 5.0 # delay in seconds
    buffersecs = 300 # size of buffer in seconds
    
    # Create buffer
    bfflen = int(buffersecs*bps)
    buff = [ 0 for x in range(bfflen) ]
    
    # Establish initial buffer pointer
    widx = int(desireddelay*bps) # pointer to write position
    ridx = 0 # pointer to read position
    
    # Prewrite empty data to buffer to be read
    blocksize = len(stream.read(CHUNK))
    for tmp in range(bfflen):
        buff[tmp] = '0' * blocksize
        
    print "Seconds per block: " + str(float(1/bps))
        
    # Write to command prompt
    write_terminal(desireddelay)

    # Preload data into output to avoid stuttering during playback
    for tmp in range(5):
        stream.write('0'*blocksize,CHUNK)

    # Loop until program terminates
    while True:
        # Write output and read next input
        buff[widx] = stream.read(CHUNK)    

        try:
            stream.write(buff[ridx],CHUNK,exception_on_underflow=True)
        except IOError: # underflow, priming the output
            print "Underflow Occured"
            stream.stop_stream()
            stream.close()
            stream = p.open(format=p.get_format_from_width(WIDTH),
                            channels=channels,
                            rate=SAMPLE_RATE,
                            input=True,
                            output=True,
                            frames_per_buffer=CHUNK)
            for i in range(5):
                stream.write('0'*blocksize,CHUNK,exception_on_underflow=False)
        
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
                ridx = int((widx - int(desireddelay*bps)) % bfflen)
                write_terminal(desireddelay)
            else:
                stream.stop_stream()
                stream.close()
                break


def main():
    # Establish pipe for delay process
    pconn1, cconn1 = Pipe()
    p1 = Process(target=delay_loop, args=(2,'default.wav',cconn1))
    p1.start()
    
    # Loop to check for change in desired delay
    while True:
        inp = raw_input(DELAY_PROMPT)
        try:
            inp = float(inp)
            if inp == -1.0: # Terminate
                pconn1.send(False)
                break
            elif inp > 0.0: # Update delay
                pconn1.send(inp)
            else:
                print "Please use a delay longer than 0 sec."   
        except:
            if "show" in inp: # Show license
                path = os.path.dirname(os.path.realpath(sys.argv[0]))
                license_file = os.path.join(path,'LICENSE')
                with open(license_file, 'r') as fin:
                    for i in range(11):
                        print(fin.readline()),
                print "See the copy of GPLv3 provided with this program"
                print "or <http://www.gnu.org/licenses/> for more details."
            else:
                print "Improper input."
    p1.join()
    
if __name__ == '__main__':
    main()
