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
import SocketServer

from optparse import OptionParser
from datetime import datetime as date
from md01_thread import *

def getTimeStampGMT(self):
    return str(date.utcnow()) + " UTC | "

class request(object):
    def __init__ (self, uid=None, ssid=None, cmd_type=None):
        #Header Fields
        self.uid    = uid       #User ID
        self.ssid   = ssid      #Subsystem ID
        self.type   = cmd_type  #Command Type


        self.cmd    = None   #
        self.az     = None
        self.el     = None

class Main_Thread(threading.Thread):
    def __init__ (self, options):
        threading.Thread.__init__(self)
        self._stop      = threading.Event()
        self.ip         = options.serv_ip
        self.port       = options.serv_port
        self.ssid       = options.ssid
        self.md01_ip    = options.md01_ip
        self.md01_port  = options.md01_port
        self.az_thresh  = options.az_thresh
        self.el_thresh  = options.el_thresh
        #self.sock      = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP Socket
        self.sock       = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP Socket
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #To allow socket reuse

        self.req    = request()
        self.valid  = 0     # 0=invalid, 1=Management Frame, 2=Antenna Frame

        #### DAEMON STATE ####
        self.state  = 'IDLE'    #IDLE, STANDBY, ACTIVE, FAULT, CALIBRATE
        self.user_con = False
        self.md01_con = False

        self.initThread()

    def initThread(self):
        self.md01_thread = MD01_Thread(self, self.ssid, self.md01_ip, self.md01_port, self.az_thresh, self.el_thresh)
        self.md01_thread.daemon = True
        self.md01_thread.start()
        time.sleep(0.1)

    def run(self):
        print self.utc_ts() + self.ssid + " Main Thread Started..."
        self.sock.bind((self.ip, self.port))
        self.sock.listen(1)
        self.Print_State()
        while (not self._stop.isSet()): 
            if self.state == 'IDLE':
                self.md01_con = self.md01_thread.get_connected()
                if (self.user_con and self.md01_con): self.set_state_standby()
                if self.user_con == False: #user is not connected
                    self.conn, self.addr = self.sock.accept()#Blocking
                    print self.utc_ts() + "User connected from: " + str(self.addr)
                    self.user_con = True
                    if (self.user_con and self.md01_con): self.set_state_standby()
                    else:  self.Print_State()
                elif self.user_con == True:
                    data = self.conn.recvfrom(1024)[0]
                    if data:
                        data = data.strip()
                        print self.utc_ts() + "User Message: " + str(data)
                        #print self.utc_ts() + "MD01 Connection Status: " + str(self.md01_con)
                    else:
                        print self.utc_ts() + "User disconnected from: " + str(self.addr)                        
                        self.user_con = False
                        self.Print_State()

            elif self.state == 'STANDBY':
                print "entered standby"
                self.md01_con = self.md01_thread.get_connected()
                
                if self.md01_con == False: #user is not connected
                    self.set_state_idle()

                if self.user_con == True:
                    print "bing"
                    data = self.conn.recvfrom(1024)[0] #blocking
                    print "bong"
                    if data:
                        data = data.strip()
                        print self.utc_ts() + "User Message: " + str(data)
                    else:
                        print self.utc_ts() + "User disconnected from: " + str(self.addr)                        
                        self.user_con = False
                        self.set_state_idle()

            elif self.state == 'ACTIVE':
                pass

    def set_state_idle(self):
        self.state = 'IDLE'
        self.Print_State()        
        
    def set_state_standby(self):
        self.state = 'STANDBY'
        self.Print_State()

    def set_state_active(self):
        pass

    def runold(self):
        print self.utc_ts() + self.ssid + " Main Thread Started..."
        print self.utc_ts() + self.ssid + " Daemon State: " + str(self.state)
        self.sock.bind((self.ip, self.port))
        self.sock.listen(1)
        while (not self._stop.isSet()):   
            if self.user_con == False: #user is not connected
                self.conn, self.addr = self.sock.accept()#Blocking
                print self.utc_ts() + "User connected from: " + str(self.addr)
                self.user_con = True
                self.md01_con = self.md01_thread.get_connected()
                if (self.user_con and self.md01_con): self.state = 'STANDBY'  #Transition to STANDBY STATE
                self.Print_State()
            if self.user_con == True:
                md01_old_con = self.md01_con
                self.md01_con = self.md01_thread.get_connected()
                if ((md01_old_con==False) and self.md01_con): self.Print_State()
                if (self.user_con and self.md01_con): self.state = 'STANDBY'  #Transition to STANDBY STATE
                data = self.conn.recvfrom(1024)[0]
                if data:
                    data = data.strip()
                    print self.utc_ts() + "User Message: " + str(data)
                    print self.utc_ts() + "MD01 Connection Status: " + str(self.md01_con)
                    ##Process data command
                else:
                    print self.utc_ts() + "User disconnected from: " + str(self.addr)                        
                    self.user_con = False
                    self.state = "IDLE"
                    self.Print_State()

    def Print_State(self):
        print self.utc_ts() + "Connection Status (USER/MD01): " + str(self.user_con) + '/' + str(self.md01_con)
        print self.utc_ts() + self.ssid + " Daemon State: " + str(self.state)

    def run_old(self):
        print self.utc_ts() + self.ssid + " Main Thread Started..."
        
        while (not self._stop.isSet()):
            if self.user_con == False: #user is not connected
                self.conn, self.addr = self.sock.accept()
                self.user_con = True
                print self.utc_ts() + "New User Connected: " + str(self.addr)
            elif self.user_con == True:
                data, addr = self.conn.recvfrom(1024) # buffer size is 1024 bytes
                if addr == None:
                    self.sock.close()
                    self.user_con = False
                    print self.utc_ts() + "User Disconnected: "
                else:
                    print self.utc_ts() + "   received from:", addr
                    print self.utc_ts() + "received message:", data
                self.valid = self.Check_Request(data)
                if self.valid == True:
                    self.Process_Request(data, addr)
        sys.exit()

    def Check_Request(self, data):
        fields = data.split(" ")
        #print fields
        #Check number of fields        
        if ((len(fields) == 2) or (len(fields) == 4)):
            try:
                self.req = request(fields[0].strip('\n'), fields[1].strip('\n'))
            except ValueError:
                print self.utc_ts() + "Error: Invalid Command Data Types"
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


    def Process_Request(self, data, addr):
        if   self.req.ssid == self.ssid: #VHF/UHF/L-Band subsystem ID
            self.Process_Command(self.md01_thread, data, addr)
        else:
            print self.utc_ts() + "This is the VUL Controller"

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

    

    def utc_ts(self):
        return str(date.utcnow()) + " UTC | MAIN-Thr | "

    def stop(self):
        self.gps_ser.close()
        self._stop.set()
        sys.quit()

    def stopped(self):
        return self._stop.isSet()

################# OLD PROCESS REQUEST FUNCTION #########################################
    def Process_Request_OLD(self, data, addr):
        if   self.req.ssid == 'VUL': #VHF/UHF/L-Band subsystem ID
            self.Process_Command(self.vul_thread, data, addr)
        elif self.req.ssid == '3M0': #3.0 m Dish Subsystem ID
            self.Process_Command(self.dish_3m0_thread, data, addr)
        elif self.req.ssid == '4M5': #4.5 m Dish Subsystem ID
            self.Process_Command(self.dish_4m5_thread, data, addr)
        elif self.req.ssid == 'WX':  #NOAA WX Subsystem ID
            pass

################# OLD CHECK REQUEST FUNCTION #########################################
    def Check_Request_OLD(self, data):
        fields = data.split(" ")
        #print fields
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

################# OLD REQUEST Object #########################################

class request_old(object):
    def __init__ (self, ssid = None, cmd = None, az = None, el = None):
        self.ssid   = ssid
        self.cmd    = cmd
        self.az     = az
        self.el     = el



