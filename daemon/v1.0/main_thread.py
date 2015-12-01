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
import socket

def getTimeStampGMT(self):
    return str(date.utcnow()) + " GMT | "

class request(object):
    def __init__ (self, ssid = None, cmd = None, az = None, el = None):
        self.ssid   = ssid
        self.cmd    = cmd
        self.az     = az
        self.el     = el

class Main_Thread(threading.Thread):
    def __init__ (self, options):
        threading.Thread.__init__(self)
        self._stop  = threading.Event()
        self.ip     = options.serv_ip
        self.port   = options.serv_port
        self.sock   = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.req    = request()
        self.cmd    = request()
        self.valid  = False

    def run(self):
        self.sock.bind((self.ip, self.port))
        while (not self._stop.isSet()):
            data, addr = self.sock.recvfrom(1024) # buffer size is 1024 bytes
            print "   received from:", addr
            print "received message:", data
            self.valid = self.Check_Request(data)
            if self.valid == True:
                #Valid Request Received, process appropriately
                print self.req.ssid, self.req.cmd, self.req.az, self.req.el
                self.Process_Request()
            #fields = data.split(" ")
            #print len(fields), fields
        sys.exit()

    def Process_Request(self):
        if   self.req.ssid == 'VUL': #VHF/UHF/L-Band subsystem ID
            pass
        elif self.req.ssid == '3M0': #3.0 m Dish Subsystem ID
            pass
        elif self.req.ssid == '4M5': #4.5 m Dish Subsystem ID
            pass
        elif self.req.ssid == 'WX':  #NOAA WX Subsystem ID
            pass


        #if   self.cmd == 'SET':     self.valid = True  #Set Command
        #elif self.cmd == 'QUERY':   self.valid = True  #Query Command
        #elif self.cmd == 'STOP':    self.valid = True  #Stop Command
        #else: 
        #    print "Error | Invalid Command Type: ", self.cmd
        #    self.valid = False

    

    def Check_Request(self, data):
        fields = data.split(" ")
        #Check number of fields        
        if ((len(fields) == 2) or (len(fields) == 4)):
            try:
                self.req = request(fields[0].strip('\n'), fields[1].strip('\n'))
            except ValueError:
                print "Error | Invalid Command Data Types"
                return False
        else: 
            print "Error | Invalid number of fields in command: ", len(fields) 
            return False
        #Validate Subsystem ID
        if ((self.req.ssid != 'VUL') and (self.req.ssid != '3M0') and (self.req.ssid != '4M5') and (self.req.ssid != 'WX')):
            print "Error | Invalid Subsystem ID Type: ", self.req.ssid
            return False
        #Validate Command Type
        if ((self.req.cmd != 'SET') and (self.req.cmd != 'QUERY') and (self.req.cmd != 'STOP')):
            print "Error | Invalid Command Type: ", self.req.cmd
            return False
        elif self.req.cmd == 'SET':
            if len(fields) != 4:
                print "Error | Invalid number of fields in command: ", len(fields) 
                return False
            
            try:
                self.req.az = float(fields[2].strip('\n'))
                self.req.el = float(fields[3].strip('\n'))
            except ValueError:
                print "Error | Invalid Command Data Types"
                return False

        return True

    def stop(self):
        self.gps_ser.close()
        self._stop.set()
        sys.quit()

    def stopped(self):
        return self._stop.isSet()


