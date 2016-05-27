#!/usr/bin/env python
#################################################
#   Title: Tracking Daemon                      #
# Project: VTGS Tracking Daemon                 #
# Version: 2.0                                  #
#    Date: May 27, 2016                         #
#  Author: Zach Leffke, KJ4QLP                  #
# Comment: This version of the Tracking Daemon  #
#           is intended to be a 1:1 interface   #
#           for the MD01.  It will run on the   #
#           Control Server 'eddie' and provide  #
#           a single interface to the MD01      #
#           controllers.                        #
#           This daemon is a protocol translator#
#################################################

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
    h_md01_ip       = "Set MD01 IP [default=%default]"
    h_md01_port     = "Set MD01 Port [default=%default]"
    
    parser.add_option("", "--serv_ip"  , dest="serv_ip"  , type="string", default="127.0.0.1"       , help=h_serv_ip)
    parser.add_option("", "--serv_port", dest="serv_port", type="int"   , default="2000"            , help=h_serv_port)
    parser.add_option("", "--md01_ip"  , dest="vul_ip"   , type="string", default="192.168.42.21"   , help=h_md01_ip)
    parser.add_option("", "--md01_port", dest="vul_port" , type="int"   , default="2000"            , help=h_md01_port)
    
    (options, args) = parser.parse_args()
    #--------END Command Line option parser------------------------------------------------------    

    serv = Main_Thread(options)
    serv.daemon = True
    serv.run()

    while 1:
        pass
    sys.exit()
    

