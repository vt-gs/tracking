#!/usr/bin/env python
#version 1.1

import socket
import os
import string
import sys
import time
from optparse import OptionParser

if __name__ == '__main__':
	
    #--------START Command Line option parser------------------------------------------------
    usage = "usage: %prog -a <Server Address> -p <Server Port> "
    parser = OptionParser(usage = usage)
    a_help = "IP address of Tracking Daemon, Default: 192.168.42.10"
    p_help = "TCP port number of Tracking Daemon, Default: 2000"
    parser.add_option("-a", dest = "ip"  , action = "store", type = "string", default = "127.0.0.1", help = a_help)
    parser.add_option("-p", dest = "port", action = "store", type = "int"   , default = "4533"     , help = p_help)
    (options, args) = parser.parse_args()
    #--------END Command Line option parser-------------------------------------------------

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP Socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((options.ip, options.port))
    s.listen(1)
 
    conn, addr = s.accept()
    connected = True
    print 'Connection address:', addr
    while 1:
        try:
            if connected == True:
                data = conn.recv(1024)
                print "received data:", data.strip('\n')
                if data.strip('\n') == 'p':
                    data = "100.000000\n20.100000\n"
                    print data
                    conn.send(data)  # echo
                elif data.strip('\n')[0] == 'P':
                    data = "\n"
                    conn.send(data)  # echo
                elif data.strip('\n') == 'q':
                    print "Gpredict Hung Up..."
                    conn.close()
                    connected = False
            else:
                print "Listening..."
                conn, addr = s.accept()
                connected = True
                print 'Connection address:', addr
        except socket.error as msg:
                print str(msg)
                connected = False
                conn.close()
        #time.sleep(0.25)
            #data = "Elevation: 20.000000\n"
            #conn.send(data)
