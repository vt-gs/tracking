#!/usr/bin/env python
##################################################
# GPS Interface
# Author: Zach Leffke
# Description: Initial GPS testing
##################################################

from optparse import OptionParser
import threading
from datetime import datetime as date
import os
import math
import sys
import string
import time
from md01 import *

def getTimeStampGMT(self):
    return str(date.utcnow()) + " GMT | "

class MD01_Thread(threading.Thread):
    def __init__ (self, ssid,ip, port, az_thresh=2, el_thresh=2):
        threading.Thread.__init__(self)
        self._stop  = threading.Event()
        self.ssid   = ssid
        self.md01   = md01(ip, port)
        self.connected = False

        self.cur_az     = 0.0
        self.cur_el     = 0.0
        self.cur_time   = None

        self.last_az    = 0.0
        self.last_el    = 0.0
        self.last_time  = None
        self.az_thresh  = az_thresh     #Azimuth Speed threshold, for error detection, deg/s
        self.el_thresh  = el_thresh     #Elevation Speed threshold, for error detection, deg/s

        self.tar_az     = 0.0
        self.tar_el     = 0.0

        self.az_motion      = False #indicates azimuth motion
        self.el_motion      = False #indicates Elevation motion
        self.az_motion_fault  = False #indicates antenna motion fault.
        self.el_motion_fault  = False #indicates antenna motion fault.
        self.thread_fault   = False #indicates unknown failure in thread
        self.thread_dormant = False


    def run(self):
        time.sleep(1)  #Give parent thread time to spool up
        print self.utc_ts() + self.ssid + " Thread Started..."
        last = None
        now = None
        while (not self._stop.isSet()):
            try:
                if self.connected == False: 
                    self.connected = self.md01.connect()
                    time.sleep(5)
                    if self.connected == True:
                        print self.utc_ts() + "Connected to " + self.ssid + " MD01 Controller"
                        self.last_time = date.utcnow()
                        self.connected, self.last_az, self.last_el = self.md01.get_status()
                        #print self.last_az, self.last_el
                        time.sleep(1)
                        
                elif self.connected == True:
                    self.cur_time = date.utcnow()
                    #delta = (now - last).total_seconds
                    self.connected, self.cur_az, self.cur_el = self.md01.get_status()
                    if self.connected == False:
                        print self.utc_ts() + "Disconnected from " + self.ssid + " MD01 Controller"
                    else:
                        az_delta = abs(self.cur_az - self.last_az)
                        el_delta = abs(self.cur_el - self.last_el)
                        time_delta = (self.cur_time - self.last_time).total_seconds()
                        #print self.last_time, self.cur_time, str(time_delta)
                        #print az_delta, el_delta, az_delta * (1.0/time_delta), el_delta * (1.0/time_delta)
                        if az_delta > 0: self.az_motion = True
                        else: self.az_motion = False

                        if el_delta > 0: self.el_motion = True
                        else: self.el_motion = False

                        if az_delta > self.az_thresh: self.az_motion_fault = True
                        if el_delta > self.el_thresh: self.el_motion_fault = True

                        if ((self.az_motion_fault == True) or (self.el_motion_fault)): self.Antenna_Motion_Fault()
                        else:
                            self.last_az = self.cur_az
                            self.last_el = self.cur_el
                            self.last_time = self.cur_time
                            #print az_delta, el_delta
                        time.sleep(0.250)
            except:
                print self.utc_ts() + "Unexpected error in thread:", self.ssid,'\n', sys.exc_info() # substitute logging
                self.connected = False
                self.thread_fault = True

        print self.utc_ts() + self.ssid + " Thread is now Dormant"
        self.thread_dormant = True
        while 1:
            time.sleep(10)

    def Antenna_Motion_Fault(self):
        print self.utc_ts() + "----ERROR! ERROR! ERROR!----"
        if self.az_motion_fault == True:
            print self.utc_ts() + "Antenna Azimuth Motion Fault in " + str(self.ssid) + " Thread"
        if self.el_motion_fault == True:
            print self.utc_ts() + "Antenna Elevation Motion Fault in " + str(self.ssid) + " Thread"
        print self.utc_ts() + "Killing Thread Now..."
        self.stop_thread()

    def get_thread_state(self):
        state = {}
        state['connected']  = self.connected
        state['dormant']    = self.thread_dormant
        state['az_motion']  = self.az_motion_fault
        state['el_motion']  = self.el_motion_fault
        state['thread']     = self.thread_fault
        return state

    def get_position(self):
        return self.cur_az, self.cur_el

    def set_position(self, az, el):
        self.tar_az = az
        self.tar_el = el
        self.md01.set_position(self.tar_az, self.tar_el)

    def utc_ts(self):
        return str(date.utcnow()) + " UTC | "

    def set_stop(self):
        self.md01.set_stop()

    def stop_thread(self):
        self.md01.set_stop()
        self.connected = self.md01.disconnect()
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()


