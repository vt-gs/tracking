#!/usr/bin/env python
#version 1.1

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
    parser.add_option("-a", dest = "ip"  , action = "store", type = "string", default = "127.0.0.1", help = a_help)
    parser.add_option("-p", dest = "port", action = "store", type = "int"   , default = "2000"     , help = p_help)
    parser.add_option("-s", dest = "ssid", action = "store", type = "string", default = "VUL"      , help = s_help)
    parser.add_option("-u", dest = "uid" , action = "store", type = "string", default = None       , help = u_help)
    (options, args) = parser.parse_args()
    #--------END Command Line option parser-------------------------------------------------

    options.ssid = options.ssid.upper()
    if (options.ssid != 'VUL') and (options.ssid != '3M0') and (options.ssid != '4M5') and (options.ssid != 'WX'):
        print 'INVALID SSID Specified'
        print 'Valid Options: \'VUL\',\'3M0\',\'4M5\',\'WX\''
        print 'Please Specify a valid SSID'
        print 'Exiting...'
        sys.exit()

    if options.uid == None:
        print 'No User ID Specified'
        print 'Please Specify a User ID'
        print 'Exiting...'
        sys.exit()

    track = vtp(options.ip, options.port, 'VUL', 2.0)

    app = QtGui.QApplication(sys.argv)
    win = MainWindow(options)
    win.set_callback(track)
    #win.setGpredictCallback(gpred)
    sys.exit(app.exec_())
    sys.exit()
