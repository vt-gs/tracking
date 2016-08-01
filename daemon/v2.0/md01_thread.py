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


from optparse import OptionParser
import threading
from datetime import datetime as date
import os
import math
import sys
import string
import time
import inspect
from md01 import *

class MD01Thread(threading.Thread):
    def __init__ (self, ssid,ip, port, poll_rate, az_thresh=2.0, el_thresh=2.0):
        threading.Thread.__init__(self)
        #self.parent = parent
        self._stop      = threading.Event()
        self.ssid       = ssid
        self.md01       = md01(ip, port)
        self.poll_rate  = poll_rate #[s]
        self.connected  = False

        self.callback = None # callback to Daemon Main Thread

        self.cur_az     = 0.0
        self.cur_el     = 0.0
        self.cur_time   = None

        self.last_az    = 0.0
        self.last_el    = 0.0
        self.last_time  = None

        self.az_rate   = 0.0
        self.el_rate   = 0.0
        self.time_delta = 0.0
        self.az_thresh  = az_thresh     #Azimuth Speed threshold, for error detection, deg/s
        self.el_thresh  = el_thresh     #Elevation Speed threshold, for error detection, deg/s

        self.tar_az     = 180.0
        self.tar_el     = 0.0

        self.set_flag = False

        self.az_motion      = False #indicates azimuth motion
        self.el_motion      = False #indicates Elevation motion
        self.az_motion_fault  = False #indicates antenna motion fault.
        self.el_motion_fault  = False #indicates antenna motion fault.
        self.thread_fault   = False #indicates unknown failure in thread
        self.thread_dormant = False
    
    def run(self):
        #time.sleep(1)  #Give parent thread time to spool up
        print self.utc_ts() + self.ssid + " MD01 Thread Started..."
        print self.utc_ts() + "  Azimuth Threshold: " + str(self.az_thresh)
        print self.utc_ts() + "Elevation Threshold: " + str(self.el_thresh)
        print self.utc_ts() + "MD-01 Poll Rate [s]: " + str(self.poll_rate)
        last = None
        now = None
        while (not self._stop.isSet()):
            try:
                if self.connected == False: 
                    self.connected = self.md01.connect()
                    #time.sleep(5)
                    if self.connected == True:
                        print self.utc_ts() + "Connected to " + self.ssid + " MD01 Controller"
                        self.last_time = date.utcnow()
                        self.connected, self.last_az, self.last_el = self.md01.get_status()
                        self.callback.set_md01_con_status(self.connected) #notify main thread of connection
                        self.set_flag = False
                        time.sleep(1)
                    else:
                        time.sleep(5)
                elif self.connected == True:
                    self.cur_time = date.utcnow()
                    self.connected, self.cur_az, self.cur_el = self.md01.get_status()
                    if self.connected == False:
                        print self.utc_ts() + "Disconnected from " + self.ssid + " MD01 Controller"
                        self.callback.set_md01_con_status(self.connected) #notify main thread of connection
                        self.set_flag = False
                    else:
                        self.time_delta = (self.cur_time - self.last_time).total_seconds()
                        self.az_rate = (self.cur_az - self.last_az) / self.time_delta
                        self.el_rate = (self.cur_el - self.last_el) / self.time_delta
                        
                        if abs(self.az_rate) > 0: self.az_motion = True
                        else: self.az_motion = False

                        if abs(self.el_rate) > 0: self.el_motion = True
                        else: self.el_motion = False

                        if abs(self.az_rate) > self.az_thresh: self.az_motion_fault = True
                        if abs(self.el_rate) > self.el_thresh: self.el_motion_fault = True

                        if ((self.az_motion_fault == True) or (self.el_motion_fault)): 
                            self.Antenna_Motion_Fault()
                        else:
                            self.last_az = self.cur_az
                            self.last_el = self.cur_el
                            self.last_time = self.cur_time
                            
                            if self.set_flag == True:  #Need to issue a set command to MD01?
                                self.set_flag = False
                                #Do current angles match target angles?
                                if ((round(self.cur_az,1) != round(self.tar_az,1)) or (round(self.cur_el,1) != round(self.tar_el,1))):
                                    #is antenna in motion?
                                    if ((self.az_motion) or (self.el_motion)): #Antenna Is in motion
                                        opposite_flag = False #indicates set command opposed to direction of motion.
                                        if (self.az_rate < 0) and (self.tar_az > self.cur_az): opposite_flag = True 
                                        elif (self.az_rate > 0) and (self.tar_az < self.cur_az): opposite_flag = True
                                        if (self.el_rate < 0) and (self.tar_el > self.cur_el): opposite_flag = True 
                                        elif (self.el_rate > 0) and (self.tar_el < self.cur_el): opposite_flag = True
                                        if opposite_flag: #Set command in opposite direction of motion
                                            print self.utc_ts()+"Set Command position opposite direction of motion"
                                            self.connected, self.cur_az, self.cur_el = self.md01.set_stop() #Stop the rotation
                                            self.set_flag = True #try to resend set command next time around the loop
                                        else: #Set command is in the direction of rotation
                                            print self.utc_ts()+"Set Command position is in direction of motion"
                                            #Set Position command does not get a feedback response from MD-01   
                                            self.connected, self.cur_az, self.cur_el = self.md01.set_position(self.tar_az, self.tar_el)
                                    else: #Antenna is stopped
                                        print self.utc_ts()+"Antenna is Stopped, sending SET command to MD01"
                                        #Set Position command does not get a feedback response from MD-01   
                                        self.connected, self.cur_az, self.cur_el = self.md01.set_position(self.tar_az, self.tar_el)

                        time.sleep(self.poll_rate)
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
            print self.utc_ts() + ("Rotation Rate: %+2.3f [deg/s] exceeded threshold: %2.3f [deg/s]" % (self.az_rate, self.az_thresh))
        if self.el_motion_fault == True:
            print self.utc_ts() + "Antenna Elevation Motion Fault in " + str(self.ssid) + " Thread"
            print self.utc_ts() + ("Rotation Rate: %+2.3f [deg/s] exceeded threshold: %2.3f [deg/s]" % (self.el_rate, self.el_thresh))            
        print self.utc_ts() + ("cur_az: %+3.2f, cur_el: %+3.2f, last_az: %+3.2f, last_el: %+3.2f, time_delta: %+3.1f [ms]" % \
                              (self.cur_az, self.cur_el, self.last_az, self.last_el, self.time_delta*1000))
        print self.utc_ts() + "Killing Thread Now..."
        self.stop_thread()

    def get_position(self):
        return self.cur_az, self.cur_el

    def get_rate(self):
        return self.az_rate, self.el_rate

    def get_connected(self):
        return self.connected

    def set_position(self, az, el):
        self.tar_az = az
        self.tar_el = el
        self.set_flag = True
        #self.md01.set_position(self.tar_az, self.tar_el)

    def set_callback(self, callback):
        self.callback = callback

    def utc_ts(self):
        return str(date.utcnow()) + " UTC | MD01 | "

    def set_stop(self):
        self.tar_az = self.cur_az
        self.tar_el = self.cur_el
        self.md01.set_stop()

    def stop_thread(self):
        self.md01.set_stop()
        self.connected = self.md01.disconnect()
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()


