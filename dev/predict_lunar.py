#!/usr/bin/env python
#########################################
#   Title: Lunar Track Prediction       #
# Project: Lunar Tracking Program
#    Date: Oct 2016                     #
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
import datetime as date
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
    ts = (date.datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S")
    #--------START Command Line option parser------------------------------------------------------
    usage  = "usage: %prog "
    parser = OptionParser(usage = usage)
    h_gs_lat    = "Ground Station Latitude [default=%default]"
    h_gs_lon    = "Ground Station Longitude [default=%default]"
    h_gs_alt    = "Ground Station Altitude [default=%default]"
    h_start     = "Simulation Start Date [default=%default]"
    h_flag      = "Lunar/Solar Flag, 0=Lunar,1=Solar [default=%default]"

    parser.add_option("", "--gs_lat", dest = "gs_lat", action = "store", type = "float", default='37.229977' , help = h_gs_lat)
    parser.add_option("", "--gs_lon", dest = "gs_lon", action = "store", type = "float", default='-80.439626', help = h_gs_lon)
    parser.add_option("", "--gs_alt", dest = "gs_alt", action = "store", type = "float", default='610'       , help = h_gs_alt)
    parser.add_option("", "--start" , dest = "start" , action = "store", type = "string", default=ts         , help = h_start)
    parser.add_option("", "--flag"  , dest = "flag"  , action = "store", type = "int"  , default='0'         , help = h_flag)
    (options, args) = parser.parse_args()
    #--------END Command Line option parser------------------------------------------------------    

    #----Define Variables ---------


    #--Setup Ground Station------------
    gs = ephem.Observer()
    gs.lat, gs.lon, gs.elevation = options.gs_lat*deg2rad, options.gs_lon*deg2rad, options.gs_alt

    #--Setup Object------------
    if options.flag == 0:
        m = ephem.Moon()
        title = 'Lunar Tracking'
    elif options.flag == 1:
        m = ephem.Sun()
        title = 'Solar Tracking'
    elif options.flag == 2:
        m = ephem.Mars()
        title = 'Mars Tracking'
    elif options.flag == 3:
        m = ephem.Jupiter()
        title = 'Jupiter Tracking'

    d = date.datetime.strptime(options.start,  "%Y-%m-%d %H:%M:%S")
    gs.date = d
    m.compute(gs)
    print "     Current Time [UTC]: {:s}".format(str(options.start))
    print "  Current Azimuth [deg]: {:3.1f}".format(dms_to_dec(m.az))
    print "Current Elevation [deg]: {:3.1f}\n".format(dms_to_dec(m.alt))

    #d = d + date.timedelta(hours=24) #Update GS Date
    #gs.date = d
    #m.compute(gs)

    rise_time = m.rise_time
    counter = 0
    while rise_time == None:
        counter += 1
        gs.date = d + date.timedelta(hours=counter) #increment time 1 hour
        m.compute(gs)
        rise_time = m.rise_time

    gs.date = rise_time
    m.compute(gs)
    print "        Rise Time [UTC]: {:s}".format(str(rise_time))
    print "     Rise Azimuth [deg]: {:3.1f}".format(dms_to_dec(m.az))
    print "   Rise Elevation [deg]: {:3.1f}\n".format(dms_to_dec(m.alt))

    gs.date = m.transit_time
    m.compute(gs)

    print "     Transit Time [UTC]: {:s}".format(str(gs.date))
    print "  Transit Azimuth [deg]: {:3.1f}".format(dms_to_dec(m.az))
    print "Transit Elevation [UTC]: {:3.1f}\n".format(dms_to_dec(m.alt))

    gs.date = m.set_time
    m.compute(gs)
    print "         Set Time [UTC]: {:s}".format(str(gs.date))
    print "      Set Azimuth [deg]: {:3.1f}".format(dms_to_dec(m.az))
    print "    Set Elevation [UTC]: {:3.1f}\n".format(dms_to_dec(m.alt))

    

    sys.exit()

    while 1:
        d = date.utcnow()
        gs.date = d
        m.compute(gs)
        os.system('clear')
        print title
        print "Time [UTC]: {:s}".format(str(d))
        print "   Azimuth: {:3.1f}".format(dms_to_dec(m.az))
        print " Elevation: {:3.1f}".format(dms_to_dec(m.alt))
        if options.flag == 0:
            print "Libration Lat: {:+3.6f}".format(dms_to_dec(m.libration_lat))
            print "Libration Lon: {:+3.6f}".format(dms_to_dec(m.libration_long))
            print "  Lunar Phase: {:3.3f}%".format(m.moon_phase*100)
        time.sleep(1)

    

    

    sys.exit()



