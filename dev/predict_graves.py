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
import datetime as date
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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

class chain(object):
    def __init__(self, start):
        self.aos        = start
        self.los        = None
        self.duration   = None
        self.max_el     = 0
        self.time_stamp = []
        self.gs_az      = []
        self.gs_el      = []
        self.graves_az  = []
        self.graves_el  = []

    def Plot(self):
        td = str(self.aos).split(" ") 
        xinch = 20
        yinch = 10
        fig=plt.figure(0, figsize=(xinch,yinch/.8))
        #plt.figure(idx)
        ax1 = plt.subplot(211)
        ax1_2 = ax1.twinx()
        ax1.set_xlabel('Time UTC')
        ax1.set_ylabel('Azimuth [degrees]', color='r')
        ax1_2.set_ylabel('Elevation [degrees]', color='b')
        #title = "Doppler Offset; %s to %s: %3.1f [km]; Access: %i ; Max El: %2.1f ; fc: %4.3f [MHz]" % \
        #        (self.gs1.name, self.gs2.name, self.baseline, idx, self.accesses[idx].max_el, fc/1e6)
        title = 'VTGS Lunar Azimuth and Elevation, {:s}'.format(td[0])
        ax1.set_title(title)
        ax1.xaxis.grid(True)
        ax1.yaxis.grid(True)
        plt.xticks(rotation=20)
        myFmt = mdates.DateFormatter('%H:%M')
        ax1.xaxis.set_major_formatter(myFmt)
        ax1.plot(self.time_stamp, self.gs_az, 'r-', label='VTGS Az')
        ax1_2.plot(self.time_stamp, self.gs_el, 'b-', label='VTGS El')

#        h1, l1 = ax1.get_legend_handles_labels()
#        ax1.legend(h1, l1, loc='center right')

        ax2 = plt.subplot(212)
        ax2_2 = ax2.twinx()
        ax2.set_xlabel('Time UTC')
        ax2.set_ylabel('Azimuth [degrees]', color='r')
        ax2_2.set_ylabel('Elevation [degrees]', color='b')
        title2 = 'GRAVES RADAR Lunar Azimuth and Elevation, {:s}'.format(td[0])
        ax2.set_title(title2)
        ax2.xaxis.grid(True)
        ax2.yaxis.grid(True)
        ax2.xaxis.set_major_formatter(myFmt)
        ax2.plot(self.time_stamp, self.graves_az, 'r-', label='GRAVES Az')
        ax2_2.plot(self.time_stamp, self.graves_el, 'b-', label='GRAVES El')
        
        self.fig = fig
        #plt.close()

        print "Saving Figures"
        path = './output/'
        if not os.path.exists(path): os.makedirs(path)
        figname = 'vtgs_graves_'+ td[0] + '_' + td[1] +'.png'
        self.fig.savefig(path + figname)    

if __name__ == '__main__':
    ts = (date.datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S")
    #--------START Command Line option parser------------------------------------------------------
    usage  = "usage: %prog "
    parser = OptionParser(usage = usage)
    h_gs_lat    = "Ground Station Latitude [default=%default]"
    h_gs_lon    = "Ground Station Longitude [default=%default]"
    h_gs_alt    = "Ground Station Altitude [default=%default]"
    h_start     = "Simulation Start Date [default=%default]"

    parser.add_option("", "--gs_lat", dest = "gs_lat", action = "store", type = "float", default='37.229977' , help = h_gs_lat)
    parser.add_option("", "--gs_lon", dest = "gs_lon", action = "store", type = "float", default='-80.439626', help = h_gs_lon)
    parser.add_option("", "--gs_alt", dest = "gs_alt", action = "store", type = "float", default='610'       , help = h_gs_alt)
    parser.add_option("", "--start" , dest = "start" , action = "store", type = "string", default=ts         , help = h_start)
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

    chain_flag  = False
    chain_start = None
    chain_stop  = None
    
    d = date.datetime.strptime(options.start,  "%Y-%m-%d %H:%M:%S")
    while not chain_flag:
        gs.date = d
        m.compute(gs)
        gs_az = dms_to_dec(m.az)
        gs_el = dms_to_dec(m.alt)
        m.compute(graves)
        graves_az = dms_to_dec(m.az)
        graves_el = dms_to_dec(m.alt)
        if ((gs_el >= 0) and (graves_el >= 0)): 
            chain_flag = True
            chain_start = d
            #break
        d = d + date.timedelta(seconds=1) #Update GS Date
    print "       Chain Start: {:s}".format(chain_start.strftime("%Y-%m-%d %H:%M:%S"))
    chain_obj = chain(chain_start)

    d = chain_start
    while chain_flag:
        gs.date = d
        m.compute(gs)
        chain_obj.time_stamp.append(d)
        gs_az = dms_to_dec(m.az)
        gs_el = dms_to_dec(m.alt)
        chain_obj.gs_az.append(gs_az)
        chain_obj.gs_el.append(gs_el)
        graves.date = d
        m.compute(graves)
        graves_az = dms_to_dec(m.az)
        graves_el = dms_to_dec(m.alt)
        chain_obj.graves_az.append(graves_az)
        chain_obj.graves_el.append(graves_el)
        if ((gs_el <= 0) or (graves_el <= 0)): 
            chain_flag = False
            chain_stop = d
            #break
        d = d + date.timedelta(seconds=1) #Update GS Date
    print "        Chain Stop: {:s}".format(chain_stop.strftime("%Y-%m-%d %H:%M:%S"))
    chain_obj.stop = chain_stop
    chain_obj.duration = (chain_stop - chain_start).total_seconds()
    print "Chain Duration [s]: {:4.1f}".format(chain_obj.duration)

    
    chain_obj.Plot()
    sys.exit()

