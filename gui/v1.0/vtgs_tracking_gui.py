#!/usr/bin/env python
import socket
import os
import string
import sys
import time
from optparse import OptionParser
from binascii import *
from vtp import *
from track_gui import *

if __name__ == '__main__':
	
    #--------START Command Line option parser------------------------------------------------
    usage = "usage: %prog -a <Server Address> -p <Server Port> "
    parser = OptionParser(usage = usage)
    s_help = "IP address of MD01 Controller, Default: 192.168.42.21"
    p_help = "TCP port number of MD01 Controller, Default: 2000"
    parser.add_option("-a", dest = "ip"  , action = "store", type = "string", default = "192.168.42.10", help = s_help)
    parser.add_option("-p", dest = "port", action = "store", type = "int"   , default = "2000"         , help = p_help)
    (options, args) = parser.parse_args()
    #--------END Command Line option parser-------------------------------------------------

    #vhf_uhf_md01 = md01(options.ip, options.port)
    #track = vtp(options.ip, options.port)

    app = QtGui.QApplication(sys.argv)
    win = MainWindow(options.ip, options.port)
    #win.setCallback(track)
    win.show()
    sys.exit(app.exec_())
    sys.exit()
