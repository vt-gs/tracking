#!/usr/bin/env python
##################################################
# GPS Interface
# Author: Zach Leffke
# Description: Initial GPS testing
##################################################

import threading
import os
import math
import sys
import string
import time
import socket

from optparse import OptionParser
from datetime import datetime as date
from md01_thread import *

def getTimeStampGMT(self):
    return str(date.utcnow()) + " UTC | "

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
        self.valid  = False

        self.vul_thread = MD01_Thread('VUL', options.vul_ip, options.vul_port)
        self.vul_thread.daemon = True
        self.vul_thread.start()

        self.dish_3m0_thread = MD01_Thread('3M0', options.dish_3m0_ip, options.dish_3m0_port)
        self.dish_3m0_thread.daemon = True
        self.dish_3m0_thread.start()

        self.dish_4m5_thread = MD01_Thread('4M5', options.dish_4m5_ip, options.dish_4m5_port)
        self.dish_4m5_thread.daemon = True
        self.dish_4m5_thread.start()

    def run(self):
        print self.utc_ts() + "Main Thread Started..."
        self.sock.bind((self.ip, self.port))
        while (not self._stop.isSet()):
            data, addr = self.sock.recvfrom(1024) # buffer size is 1024 bytes
            #print self.utc_ts() + "   received from:", addr
            #print self.utc_ts() + "received message:", data
            self.valid = self.Check_Request(data)
            if self.valid == True:
                #Valid Request Received, process appropriately
                #print self.req.ssid, self.req.cmd, self.req.az, self.req.el
                self.Process_Request(data, addr)
            #fields = data.split(" ")
            #print len(fields), fields
        sys.exit()

    def Process_Request(self, data, addr):
        if   self.req.ssid == 'VUL': #VHF/UHF/L-Band subsystem ID
            self.Process_Command(self.vul_thread, data, addr)
        elif self.req.ssid == '3M0': #3.0 m Dish Subsystem ID
            self.Process_Command(self.dish_3m0_thread, data, addr)
        elif self.req.ssid == '4M5': #4.5 m Dish Subsystem ID
            self.Process_Command(self.dish_4m5_thread, data, addr)
        elif self.req.ssid == 'WX':  #NOAA WX Subsystem ID
            pass

    def Process_Command(self, thr, data, addr):
        az = 0 
        el = 0
        if thr.connected == True:
            if   self.req.cmd == 'SET':
                thr.set_position(self.req.az, self.req.el)
                az, el = thr.get_position()
            elif self.req.cmd == 'QUERY':
                az, el = thr.get_position()
                #print az, el
            elif self.req.cmd == 'STOP':
                thr.set_stop()
                time.sleep(0.01)
                az, el = thr.get_position()
            
        self.Send_Feedback(thr, az, el, data, addr)

    def Send_Feedback(self,thr, az, el, data, addr):
        msg = thr.ssid + " QUERY " + str(az) + " " + str(el) + "\n"
        self.sock.sendto(msg, addr)

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

    def utc_ts(self):
        return str(date.utcnow()) + " UTC | "

    def stop(self):
        self.gps_ser.close()
        self._stop.set()
        sys.quit()

    def stopped(self):
        return self._stop.isSet()


