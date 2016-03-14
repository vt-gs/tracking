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
import inspect
from md01 import *

def getTimeStampGMT(self):
    return str(date.utcnow()) + " GMT | "

class MD01_Thread(threading.Thread):
    def __init__ (self, ssid,ip, port, az_thresh=2.75, el_thresh=2.75):
        threading.Thread.__init__(self)
        self._stop  = threading.Event()
        self.lock   = threading.Lock()
        self.ssid   = ssid
        self.md01   = md01(ip, port)
        self.connected = False

        self.cur_az     = 180.0
        self.cur_el     = 0.0
        self.cur_time   = None

        self.last_az    = 180.0
        self.last_el    = 0.0
        self.last_time  = None

        self.az_delta   = 0.0
        self.el_delta   = 0.0
        self.az_rate    = 0.0
        self.el_rate    = 0.0
        self.time_delta = 0.0
        self.az_thresh  = az_thresh     #Azimuth Speed threshold, for error detection, deg/s
        self.el_thresh  = el_thresh     #Elevation Speed threshold, for error detection, deg/s

        self.tar_az     = 180.0
        self.tar_el     = 0.0

        self.set_motion = False #indicates daemon received command to move antennas
        self.motion_set = False #indicates daemon has issued set_position command
        self.stop_motion = False    #indicates daemon received command to stop antenna motion
        self.motion_stop = False    #indicates daemon has issues set_stop command

        self.az_locked  = False #indicates cur_az != tar_az
        self.el_locked  = False #indicates cur_el != tar_el

        self.az_motion      = False #indicates azimuth motion based on feedback
        self.el_motion      = False #indicates Elevation motion based on feedback

        self.az_motion_fault  = False #indicates antenna azimuth motion fault.
        self.el_motion_fault  = False #indicates antenna elevation motion fault.

        self.thread_fault   = False #indicates unknown failure in thread
        self.thread_dormant = False
        
        


    def run(self):
        time.sleep(1)  #Give parent thread time to spool up
        print self.utc_ts() + "Thread Started..."
        last = None
        now = None
        set_flag = 0
        while (not self._stop.isSet()):
            try:
                if self.connected == False: 
                    self.connected = self.md01.connect()
                    time.sleep(5)
                    if self.connected == True:
                        print self.utc_ts() + "Connected to " + self.ssid + " MD01 Controller"
                        self.last_time = date.utcnow()
                        self.connected, self.last_az, self.last_el = self.md01.get_status()
                        time.sleep(1)
                elif self.connected == True:
                    #Get current time                    
                    self.cur_time = date.utcnow()
                    #Get current position
                    self.connected, self.cur_az, self.cur_el = self.md01.get_status()

                    if self.connected == False:
                        print self.utc_ts() + "Disconnected from " + self.ssid + " MD01 Controller"
                        set_flag = 0
                    else:
                        if self.stop_motion:
                            self.md01.set_stop()
                            print self.utc_ts() + "Stop Command Issued..."
                            self.stop_motion = False
                            self.motion_stop = True

                        #Check if current pointing is locked on target angles
                        if round(self.cur_az,1) == round(self.tar_az,1): 
                            self.az_locked = True
                        else:  
                            self.az_locked = False
                        if round(self.cur_el,1) == round(self.tar_el,1): 
                            self.el_locked = True
                        else: 
                            self.el_locked = False

                        #if antennas are aligned with target point and the set motion command had been issued, reset motion_set
                        if (self.az_locked and self.el_locked and self.motion_set): self.motion_set = False
                        #if (self.az_locked and self.el_locked and self.motion_stop): self.motion_stop = False


                        self.time_delta = (self.cur_time - self.last_time).total_seconds()
                        self.az_delta = self.tar_az - self.cur_az
                        self.az_rate = (self.cur_az - self.last_az) / self.time_delta
                        self.el_delta = self.tar_el - self.cur_el
                        self.el_rate = (self.cur_el - self.last_el) / self.time_delta
                        
                        if abs(self.az_rate) > 0: self.az_motion = True
                        else: self.az_motion = False

                        if abs(self.el_rate) > 0: self.el_motion = True
                        else: self.el_motion = False

                        if abs(self.az_rate) > self.az_thresh: self.az_motion_fault = True
                        if abs(self.el_rate) > self.el_thresh: self.el_motion_fault = True

                        if ((self.az_motion_fault) or (self.el_motion_fault)): 
                            self.Antenna_Motion_Fault()
                            set_flag = 0
                        else:
                            if self.motion_stop:
                                #print self.utc_ts() + "Stopping Motion...", self.cur_az, self.cur_el
                                if ((self.az_motion == False) and (self.el_motion == False)):
                                    print "%sAntenna Stopped, az=%3.1f, el=%3.1f" % (self.utc_ts(), self.cur_az, self.cur_el)
                                    self.tar_az = self.cur_az
                                    self.tar_el = self.cur_el
                                    self.motion_stop = False
                                    self.motion_set = False

                            
                                    
                            #save last variables
                            self.last_az = self.cur_az
                            self.last_el = self.cur_el
                            self.last_time = self.cur_time
                            #set_flag += 1
                            #if set_flag == 4:
                            #    set_flag = 0
                            

                            #print "  Azimuth:\t%3.2f\t%3.1f\t%3.1f\t%s\t%s" %(self.az_rate, self.cur_az, self.tar_az, self.az_locked, self.motion_set)
                            #print "Elevation:\t%3.2f\t%3.1f\t%3.1f\t%s\t%s" %(self.el_rate, self.cur_el, self.tar_el, self.el_locked, self.motion_set)


                            if self.motion_set==True: # antennas should be moving
                                if self.az_locked == False: #antennas not locked on azimuth
                                    if self.az_motion == False: #antennas not moving
                                        print "%sAzimuth Stopped before reaching target; cur: %3.1f, tar: %3.1f" % (self.utc_ts(),self.cur_az, self.tar_az)
                                if self.el_locked == False: #antennas not locked on elevation
                                    if self.el_motion == False: #antennas not moving
                                        print "%sElevation Stopped before reaching target; cur: %3.1f, tar: %3.1f" % (self.utc_ts(), self.cur_el, self.tar_el)

                            if self.set_motion == True:  
                                self.md01.set_position(self.tar_az, self.tar_el)
                                self.motion_set = True
                                self.set_motion = False
                            

                            #set_flag += 1
                            #self.last_az = self.cur_az
                            #self.last_el = self.cur_el
                            #self.last_time = self.cur_time
                            #if set_flag == 4:
                            #    set_flag = 0
                            #    if ((round(self.cur_az,1) != round(self.tar_az,1)) or (round(self.cur_el,1) != round(self.tar_el,1))):
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
            print self.utc_ts() + ("Rotation Rate: %+2.3f [deg/s] exceeded threshold: %2.3f [deg/s]" % (self.az_rate, self.az_thresh))
        if self.el_motion_fault == True:
            print self.utc_ts() + "Antenna Elevation Motion Fault in " + str(self.ssid) + " Thread"
            print self.utc_ts() + ("Rotation Rate: %+2.3f [deg/s] exceeded threshold: %2.3f [deg/s]" % (self.el_rate, self.el_thresh))            
        print self.utc_ts() + ("cur_az: %+3.2f, cur_el: %+3.2f, last_az: %+3.2f, last_el: %+3.2f, time_delta: %+3.1f [ms]" % \
                              (self.cur_az, self.cur_el, self.last_az, self.last_el, self.time_delta*1000))
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
        #time.sleep(100)
        #self.md01.set_position(self.tar_az, self.tar_el)
        self.set_motion = True

    def utc_ts(self):
        return str(date.utcnow()) + " UTC | " + self.ssid + " | "

    def set_stop(self):
        #self.md01.set_stop()
        self.stop_motion = True
        #self.tar_az = self.cur_az
        #self.tar_el = self.cur_el
        #self.az_locked = True
        #self.el_locked = True

    def stop_thread(self):
        self.md01.set_stop()
        self.connected = self.md01.disconnect()
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()


