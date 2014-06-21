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

import alsaaudio
import audioop
from multiprocessing import Process, Pipe
import os
import sys
import time

DELAY_PROMPT = 'Enter your desired delay in seconds. Enter -1 to quit.\n'
SAMPLE_RATE = 44100
PERIOD_SIZE = 160

COPYRIGHT = ('RadioDelay (aka Verne-Be-Gone)\n'
             'Copyright (C) 2014  Steven Young <stevenryoung@gmail.com>\n'
             'This program comes with ABSOLUTELY NO WARRANTY.\n'
             'This is free software, and you are welcome to redistribute it\n'
             'under certain conditions; type "show details" for more info\n')

def delay_loop(channels=2, filename='default.wav', conn=[]):

    # Initialize Audio Input
    inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL)
    inp.setchannels(channels) # 1==mono, 2==stereo
    inp.setrate(SAMPLE_RATE) # 44100 Hz
    inp.setformat(alsaaudio.PCM_FORMAT_S16_LE) # 16 bit little endian samples
    inp.setperiodsize(PERIOD_SIZE)
   
    # Initialize Audio Output 
    out = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK)
    out.setchannels(channels)
    out.setrate(SAMPLE_RATE)
    out.setformat(alsaaudio.PCM_FORMAT_S16_LE)
    blocksize = PERIOD_SIZE * 2 * channels
    out.setperiodsize(PERIOD_SIZE)

    # Establish some parameters
    bps = float(SAMPLE_RATE)/float(PERIOD_SIZE) #275.625 # Blocks collected per second
    desireddelay = 5.0 # delay in seconds
    buffersecs = 300 # size of buffer in seconds
    
    # Create buffer
    bfflen = buffersecs*bps
    data = [ 0 for x in range(int(bfflen)) ]
    
    # Establish initial buffer pointer
    widx = int(desireddelay*bps) # pointer to write position
    ridx = 0 # pointer to read position
    
    # Prewrite empty data to buffer to be read
    for tmp in range(int(bfflen)):
        data[tmp] = '0' * blocksize
        
    # Preload data into output to avoid stuttering during playback
    for tmp in range(10):
        out.write('0'*blocksize)
        
    # Write to command prompt
    os.system('clear')
    print COPYRIGHT
    print "Delay (seconds):", desireddelay
    print DELAY_PROMPT
    
    # Loop until program terminates
    while True:
        # Write output and read next input
        out.write(data[ridx])
        l, data[widx] = inp.read()
        
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
            else:
                break
            os.system('clear')
            print COPYRIGHT
            print "Delay (seconds):", desireddelay
            print DELAY_PROMPT


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
