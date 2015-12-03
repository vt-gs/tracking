#!/usr/bin/env python
#########################################
#   Title: Tracking Daemon              #
# Project: VTGS Tracking Daemon         #
# Version: 1.0                          #
#    Date: Dec 1, 2015                  #
#  Author: Zach Leffke, KJ4QLP          #
# Comment: This is the initial version  # 
#          of the Tracking Daemon.      #
#########################################

import math
import string
import time
import sys
import csv
import os
import datetime

from optparse import OptionParser
from md01 import *
from main_thread import *

if __name__ == '__main__':
    #--------START Command Line option parser------------------------------------------------------
    usage  = "usage: %prog "
    parser = OptionParser(usage = usage)
    h_serv_ip       = "Set Service IP [default=%default]"
    h_serv_port     = "Set Service Port [default=%default]"
    h_vul_ip        = "Set VHF/UHF MD01 IP [default=%default]"
    h_vul_port      = "Set VHF/UHF MD01 Port [default=%default]"
    h_3m0_ip        = "Set 3.0m MD01 IP [default=%default]"
    h_3m0_port      = "Set 3.0m MD01 Port [default=%default]"
    h_4m5_ip        = "Set 4.5m MD01 IP [default=%default]"
    h_4m5_port      = "Set 4.5m MD01 Port [default=%default]"
    h_wx_ip         = "Set WX Controller IP [default=%default]"
    h_wx_port       = "Set WX Controller Port [default=%default]"
    
    parser.add_option("", "--serv_ip"  , dest="serv_ip"  , type="string", default="127.0.0.1" , help=h_serv_ip)
    parser.add_option("", "--serv_port", dest="serv_port", type="int"   , default="2000"      , help=h_serv_port)
    parser.add_option("", "--vul_ip"  , dest="vul_ip"  , type="string", default="192.168.42.21" , help=h_vul_ip)
    parser.add_option("", "--vul_port", dest="vul_port", type="int"   , default="2000"          , help=h_vul_port)
    parser.add_option("", "--3m0_ip"  , dest="3m0_ip"  , type="string", default="192.168.42.31" , help=h_3m0_ip)
    parser.add_option("", "--3m0_port", dest="3m0_port", type="int"   , default="2000"          , help=h_3m0_port)
    parser.add_option("", "--4m5_ip"  , dest="4m5_ip"  , type="string", default="192.168.42.41" , help=h_4m5_ip)
    parser.add_option("", "--4m5_port", dest="4m5_port", type="int"   , default="2000"          , help=h_4m5_port)
    parser.add_option("", "--wx_ip"   , dest="wx_ip"   , type="string", default="192.168.42.51" , help=h_wx_ip)
    parser.add_option("", "--wx_port" , dest="wx_port" , type="int"   , default="2000"          , help=h_wx_port)
    
    (options, args) = parser.parse_args()
    #--------END Command Line option parser------------------------------------------------------    

    serv = Main_Thread(options)
    serv.daemon = True
    serv.run()

    while 1:
        pass
    sys.exit()
    

