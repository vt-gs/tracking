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
    def __init__ (self, ssid,ip, port, az_thresh, el_thresh):
        threading.Thread.__init__(self)
        self._stop  = threading.Event()
        self.ssid   = ssid
        self.md01   = md01(ip, port)
        self.connected = False

        self.cur_az     = 0.0
        self.cur_el     = 0.0

        self.last_az    = 0.0
        self.last_el    = 0.0
        self.az_thresh  = az_thresh     #Azimuth Speed threshold, for error detection, deg/s
        self.el_thresh  = el_thresh     #Elevation Speed threshold, for error detection, deg/s

        self.tar_az     = 0.0
        self.tar_el     = 0.0

        self.motion = False #indicates antennas in motion
        self.motion_fault  = False #indicates antenna motion fault.
        self.thread_fault  = False #indicates unknown failure in thread


    def run(self):
        time.sleep(1)  #Give parent thread time to spool up
        print self.ssid, "Thread Started..."
        while (not self._stop.isSet()):
            try:
                if self.connected == False: 
                    self.connected = self.md01.connect()
                    #time.sleep(0.010)
                    if self.connected == True:
                        print "Connected to " + self.ssid + " MD01 Controller"
                        time.sleep(0.10)
                        self.connected, self.last_az, self.last_el = self.md01.get_status()
                        #print self.last_az, self.last_el
                        time.sleep(1)
                if self.connected == True:
                    self.connected, self.cur_az, self.cur_el = self.md01.get_status()
                    if self.connected == False:
                        print "Disconnected from " + self.ssid + " MD01 Controller"
                    else:
                        az_delta = abs(self.cur_az - self.last_az)
                        el_delta = abs(self.cur_el - self.last_el)
                        if az_delta > self.az_thresh:  self.Antenna_Motion_Fault()
                        elif el_delta > self.el_thresh:  self.Antenna_Motion_Fault()
                        else:
                            self.last_az = self.cur_az
                            self.last_el = self.cur_el
                            #print az_delta, el_delta
                        time.sleep(1)
            except:
                print "Unexpected error in thread:", self.ssid,'\n', sys.exc_info() # substitute logging
                self.connected = False
                self.thread_fault = True

        while 1:
            time.sleep(1)

    def Antenna_Motion_Fault(self):
        self.motion_fault = True
        print "----ERROR! ERROR! ERROR!----"
        print "Antenna Motion Fault in " + str(self.ssid) + " Thread"
        print "Killing Thread Now..."
        self.stop_thread()

    def get_position(self):
        return self.cur_az, self.cur_el

    def set_position(self, az, el):
        self.tar_az = az
        self.tar_el = el
        self.md01.set_position(self.tar_az, self.tar_el)

    def set_stop(self):
        self.motion = False
        self.md01.set_stop()

    def stop_thread(self):
        self.md01.set_stop()
        self.md01.disconnect()
        self._stop.set()
        sys.quit()

    def stopped(self):
        return self._stop.isSet()


