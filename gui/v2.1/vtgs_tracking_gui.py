#!/usr/bin/env python
#version 2.1

import socket
import os
import string
import sys
import time
from optparse import OptionParser
from binascii import *
from track_gui import *
from vtp import *

if __name__ == '__main__':
	
    #--------START Command Line option parser------------------------------------------------
    usage = "usage: %prog -a <Server Address> -p <Server Port> "
    parser = OptionParser(usage = usage)
    a_help = "Set Tracking Daemon IP [default=%default]"
    p_help = "Set Tracking Daemon Port [default=%default]"
    s_help = "Set SSID [default=%default]"
    u_help = "Set User ID [default=%default]"
    parser.add_option("-a", dest = "ip"  , action = "store", type = "string", default = "192.168.42.10" , help = a_help)
    parser.add_option("-p", dest = "port", action = "store", type = "int"   , default = None            , help = p_help)
    parser.add_option("-s", dest = "ssid", action = "store", type = "string", default = "VUL"           , help = s_help)
    parser.add_option("-u", dest = "uid" , action = "store", type = "string", default = None            , help = u_help)
    (options, args) = parser.parse_args()
    #--------END Command Line option parser-------------------------------------------------

    if options.uid == None:
        print 'No User ID Specified'
        print 'Please Specify a User ID'
        print 'Exiting...'
        sys.exit()

    options.ssid = options.ssid.upper()
    if (options.ssid != 'VUL') and (options.ssid != '3M0') and (options.ssid != '4M5') and (options.ssid != 'WX'):
        print 'INVALID SSID Specified'
        print 'Valid Options: \'VUL\',\'3M0\',\'4M5\',\'WX\''
        print 'Please Specify a valid SSID'
        print 'Exiting...'
        sys.exit()

    if options.ssid == 'VUL':
        port = int(2000)
    elif options.ssid == '3M0':
        port = int(2001)
    elif options.ssid == '4M5':
        port = int(2002)
    elif options.ssid == 'WX':
        port = int(2003)

    if options.port != None:
        port = options.port

    track = vtp(options.ip, port, options.uid, options.ssid, 2.0)

    app = QtGui.QApplication(sys.argv)
    win = MainWindow(options)
    win.set_callback(track)
    #win.setGpredictCallback(gpred)
    sys.exit(app.exec_())
    sys.exit()
