#!/usr/bin/env python
#########################################
#   Title: Lunar Track                  #
# Project: Lunar Tracking Program
#    Date: Aug 2016                     #
#  Author: Zach Leffke, KJ4QLP          #
#########################################

import math
import string
import time
import sys
import csv
import os
import ephem

from optparse import OptionParser
from datetime import datetime as date
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import *
from mpl_toolkits.basemap import Basemap
import numpy as np

deg2rad = math.pi / 180
rad2deg = 180 / math.pi
c       = float(299792458)    #[m/s], speed of light

def dms_to_dec(DMS):
    data = str(DMS).split(":")
    degrees = float(data[0])
    minutes = float(data[1])
    seconds = float(data[2])
    if degrees < 0 : DEC = -(seconds/3600) - (minutes/60) + degrees
    else: DEC = (seconds/3600) + (minutes/60) + degrees
    return DEC

if __name__ == '__main__':
    #--------START Command Line option parser------------------------------------------------------
    usage  = "usage: %prog "
    parser = OptionParser(usage = usage)
    h_gs_lat    = "Ground Station Latitude [default=%default]"
    h_gs_lon    = "Ground Station Longitude [default=%default]"
    h_gs_alt    = "Ground Station Altitude [default=%default]"
    h_flag      = "Lunar/Solar Flag, 0=Lunar,1=Solar [default=%default]"

    parser.add_option("", "--gs_lat", dest = "gs_lat", action = "store", type = "float", default='37.229977' , help = h_gs_lat)
    parser.add_option("", "--gs_lon", dest = "gs_lon", action = "store", type = "float", default='-80.439626', help = h_gs_lon)
    parser.add_option("", "--gs_alt", dest = "gs_alt", action = "store", type = "float", default='610'       , help = h_gs_alt)
    parser.add_option("", "--flag"  , dest = "flag"  , action = "store", type = "int"  , default='0'         , help = h_flag)
    (options, args) = parser.parse_args()
    #--------END Command Line option parser------------------------------------------------------    

    m = ephem.Moon()

    #--Setup VTGS -----------------
    gs = ephem.Observer()
    gs.lat, gs.lon, gs.elevation = options.gs_lat*deg2rad, options.gs_lon*deg2rad, options.gs_alt

    #--Setup GRAVES -----------------
    graves = ephem.Observer()
    graves.lat = 47.347980*deg2rad
    graves.lon = 5.515095*deg2rad
    graves.elevation = 200

    chain = False

    while 1:
        d = date.utcnow()
        gs.date = d
        m.compute(gs)
        gs_az = dms_to_dec(m.az)
        gs_el = dms_to_dec(m.alt)
        graves.date = d
        m.compute(graves)
        graves_az = dms_to_dec(m.az)
        graves_el = dms_to_dec(m.alt)
        graves_phase = m.moon_phase*100

        if ((gs_el > 0) and (graves_el > 0)): chain = True
        else: chain = False

        os.system('clear')
        print "GRAVES RADAR Lunar Illumination"
        print "Time [UTC]: {:s}".format(str(d))
        print "    GS   Azimuth: {:3.1f}".format(gs_az)
        print "    GS Elevation: {:3.1f}".format(gs_el)
        print "GRAVES   Azimuth: {:3.1f}".format(graves_az)
        print "GRAVES Elevation: {:3.1f}".format(graves_el)
        print "    Chain Status: {:s}".format(str(chain))
        if options.flag == 0:
            print "Libration Lat: {:+3.6f}".format(dms_to_dec(m.libration_lat))
            print "Libration Lon: {:+3.6f}".format(dms_to_dec(m.libration_long))
            print "  Lunar Phase: {:3.3f}%".format(m.moon_phase*100)
        time.sleep(1)

    

    

    sys.exit()


