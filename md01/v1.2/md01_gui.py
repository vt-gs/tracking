#!/usr/bin/env python
import socket
import os
import string
import sys
import time
from optparse import OptionParser
from binascii import *
from md01 import *
from track_gui import *
from predict import *

if __name__ == '__main__':
	
    #--------START Command Line option parser------------------------------------------------
    usage = "usage: %prog -a <Server Address> -p <Server Port> "
    parser = OptionParser(usage = usage)
    s_help = "IP address of MD01 Controller, Default: 192.168.42.21"
    p_help = "TCP port number of MD01 Controller, Default: 2000"
    pred_ip_h    = "IP address of Predict Server, Default: 127.0.0.1"
    pred_port_h  = "Port Number of Predict Server, Default: 1210"
    parser.add_option("-a", dest = "ip"  , action = "store", type = "string", default = "192.168.42.21", help = s_help)
    parser.add_option("-p", dest = "port", action = "store", type = "int"   , default = "2000"         , help = p_help)
    parser.add_option("--predict-ip"  , dest = "pred_ip"   , action = "store", type = "string", default = "127.0.0.1", help = pred_ip_h)
    parser.add_option("--predict-port", dest = "pred_port" , action = "store", type = "int"   , default = "1210"     , help = pred_port_h)
    (options, args) = parser.parse_args()
    #--------END Command Line option parser-------------------------------------------------

    vhf_uhf_md01 = md01(options.ip, options.port)
    predict = predict(options.pred_ip, options.pred_port)

    app = QtGui.QApplication(sys.argv)
    win = MainWindow(options.ip, options.port)
    win.setMD01Callback(vhf_uhf_md01)
    win.setPredictCallback(predict)
    sys.exit(app.exec_())
    sys.exit()
