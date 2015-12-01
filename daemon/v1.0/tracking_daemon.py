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

from optparse import OptionParser
import datetime
from md01 import *

if __name__ == '__main__':
    #--------START Command Line option parser------------------------------------------------------
    usage  = "usage: %prog "
    parser = OptionParser(usage = usage)
    h_filename      = "Set filename [default=%default]"
    h_tlefile       = "Set TLE filename [default=%default]"
    h_gs_lat        = "Ground Station Latitude [default=%default]"
    h_gs_lon        = "Ground Station Longitude [default=%default]"
    h_gs_alt        = "Ground Station Altitude [default=%default]"
    h_dn_center  = "Transponder Center Frequency [default=%default]"
    h_up_center  = "Transponder Center Frequency [default=%default]"

    parser.add_option("", "--filename", dest="filename", type="string", default="fo29_20151111_193006.940360285_UTC_250k_sigA.csv", help=h_filename)
    parser.add_option("", "--tlefile", dest="tlefile", type="string", default="fo29_20151111.tle", help=h_tlefile)
    parser.add_option("", "--gs_lat", dest = "gs_lat", action = "store", type = "float", default='37.229977' , help = h_gs_lat)
    parser.add_option("", "--gs_lon", dest = "gs_lon", action = "store", type = "float", default='-80.439626', help = h_gs_lon)
    parser.add_option("", "--gs_alt", dest = "gs_alt", action = "store", type = "float", default='610'       , help = h_gs_alt)
    parser.add_option("", "--dn_center", dest = "dn_center", action = "store", type = "float", default='435.85e6' , help = h_dn_center)
    parser.add_option("", "--up_center", dest = "up_center", action = "store", type = "float", default='145.95e6' , help = h_up_center)
    (options, args) = parser.parse_args()
    #--------END Command Line option parser------------------------------------------------------    

    vul_ip = 192.168.42.21
    vul_port = 2000
    

    vul_md01 = md01(vul_ip, vul_port)
    sys.exit()


