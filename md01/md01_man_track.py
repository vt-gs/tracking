#!/usr/bin/env python
import socket
import os
import string
import sys
import time
import curses
import threading
from optparse import OptionParser
from binascii import *
from md01 import *
#from curses_display import *


if __name__ == '__main__':
	
    #--------START Command Line option parser------------------------------------------------
    usage = "usage: %prog -a <Server Address> -p <Server Port> "
    parser = OptionParser(usage = usage)
    s_help = "IP address of tracker, Default: 192.168.42.21"
    p_help = "TCP port number of tracker, Default: 2000"
    parser.add_option("-a", dest = "ip"  , action = "store", type = "string", default = "192.168.42.21", help = s_help)
    parser.add_option("-p", dest = "port", action = "store", type = "int"   , default = "2000"         , help = p_help)
    (options, args) = parser.parse_args()
    #--------END Command Line option parser-------------------------------------------------
    
    #tt = Tracker_Thread(options)
    #dt = Display_Thread(options, tt)
    #tt.daemon = True
    #dt.daemon = True
    #tt.start()
    #dt.run()
    
    vhf_uhf_md01 = md01(options.ip, options.port)
    vhf_uhf_md01.connect()

    while True:
        x = raw_input('Send command: 1=stop, 2=status, 3=set: ')
        if (x == '1'):  
            cur_az, cur_el = vhf_uhf_md01.set_stop()
            print cur_az, cur_el
        elif (x == '2'):  
            cur_az, cur_el = vhf_uhf_md01.get_status()
            print cur_az, cur_el
        elif (x == '3'):
            target_az = raw_input('  Enter Azimuth: ')
            target_el = raw_input('Enter Elevation: ')
            target_az = float(target_az)
            target_el = float(target_el)
            vhf_uhf_md01.set_position(target_az, target_el)            
        elif (x == 'q'):
            print "Received \'Quit\' Command"
            print "Closing Socket, Terminating Program..."
            vhf_uhf_md01.disconnect()
            sys.exit()
    
    sys.exit()

