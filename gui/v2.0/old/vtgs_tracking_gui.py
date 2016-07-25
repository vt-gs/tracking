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
    parser.add_option("-a", dest = "ip"  , action = "store", type = "string", default = "127.0.0.1", help = a_help)
    parser.add_option("-p", dest = "port", action = "store", type = "int"   , default = "2000"     , help = p_help)
    (options, args) = parser.parse_args()
    #--------END Command Line option parser-------------------------------------------------

    track = vtp(options.ip, options.port, 'VUL', 2.0)

    app = QtGui.QApplication(sys.argv)
    win = MainWindow(options.ip, options.port)
    win.setCallback(track)
    #win.setGpredictCallback(gpred)
    sys.exit(app.exec_())
    sys.exit()
