#!/usr/bin/env python
import socket
import os
import string
import sys
import time
import curses
import threading
from binascii import *
from optparse import OptionParser

class md01(object):
    def __init__ (self, ip, port, timeout = 1.0, retries = 2):
        self.ip         = ip        #IP Address of MD01 Controller
        self.port       = port      #Port number of MD01 Controller
        self.sock       = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP Socket
        self.timeout    = timeout   #Socket Timeout interval, default = 1.0 seconds
        self.sock.settimeout(timeout)   #set socket timeout
        self.retries    = retries   #Number of times to attempt reconnection, default = 2
        self.cmd_az     = 0         #Commanded Azimuth, used in Set Position Command
        self.cmd_el     = 0         #Commanded Elevation, used in Set Position command
        self.cur_az     = 0         #  Current Azimuth, in degrees, from feedback
        self.cur_el     = 0         #Current Elevation, in degrees, from feedback
        self.ph         = 10        #  Azimuth Resolution, in pulses per degree, from feedback, default = 10
        self.pv         = 10        #Elevation Resolution, in pulses per degree, from feedback, default = 10
        self.feedback   = ''        #Feedback data from socket
        self.stop_cmd   = bytearray()   #Stop Command Message
        self.status_cmd = bytearray()   #Status Command Message
        self.set_cmd    = bytearray()   #Set Command Message
        for x in [0x57,0,0,0,0,0,0,0,0,0,0,0x0F,0x20]: self.stop_cmd.append(x)
        for x in [0x57,0,0,0,0,0,0,0,0,0,0,0x1F,0x20]: self.status_cmd.append(x)
        for x in [0x57,0,0,0,0,0x0a,0,0,0,0,0x0a,0x2F,0x20]: self.set_cmd.append(x) #PH=PV=0x0a, 0x0a = 10, BIG-RAS/HR is 10 pulses per degree

    def connect(self):
        #connect to md01 controller
        try:
            self.sock.connect((self.ip, self.port))
            #upon connection, get status to determine current antenna position
            self.get_status()
        except socket.error as msg:
            print "Exception Thrown: " + str(msg) + " (" + str(self.timeout) + "s)"
            print "Unable to connect to MD01 at IP: " + str(self.ip) + ", Port: " + str(self.port)  
            print "Terminating Program..."
            sys.exit()

    def disconnect(self):
        #disconnect from md01 controller
        self.sock.close()
    
    def get_status(self):
        #get azimuth and elevation feedback from md01
        try:
            self.sock.send(self.status_cmd) 
            self.feedback = self.recv_data()          
        except socket.error as msg:
            print "Exception Thrown: " + str(msg) + " (" + str(self.timeout) + "s)"
            print "Closing socket, Terminating program...."
            self.sock.close()
            sys.exit()
        self.convert_feedback()  
        return self.cur_az, self.cur_el  

    def set_stop(self):
        #stop md01 immediately
        try:
            self.sock.send(self.stop_cmd) 
            self.feedback = self.recv_data()          
        except socket.error as msg:
            print "Exception Thrown: " + str(msg) + " (" + str(self.timeout) + "s)"
            print "Closing socket, Terminating program...."
            self.sock.close()
            sys.exit()
        self.convert_feedback()
        return self.cur_az, self.cur_el   

    def set_position(self, az, el):
        #set azimuth and elevation of md01
        self.cmd_az = az
        self.cmd_el = el
        self.format_set_cmd()
        try:
            self.sock.send(self.set_cmd) 
        except socket.error as msg:
            print "Exception Thrown: " + str(msg)
            print "Closing socket, Terminating program...."
            self.sock.close()
            sys.exit()

    def recv_data(self):
        #receive socket data
        feedback = ''
        while True:
            c = self.sock.recv(1)
            if hexlify(c) == '20':
                feedback += c
                break
            else:
                feedback += c
        print hexlify(feedback)
        return feedback

    def convert_feedback(self):
        h1 = ord(self.feedback[1])
        h2 = ord(self.feedback[2])
        h3 = ord(self.feedback[3])
        h4 = ord(self.feedback[4])
        #print h1, h2, h3, h4
        self.cur_az = (h1*100.0 + h2*10.0 + h3 + h4/10.0) - 360.0
        self.ph = ord(self.feedback[5])

        v1 = ord(self.feedback[6])
        v2 = ord(self.feedback[7])
        v3 = ord(self.feedback[8])
        v4 = ord(self.feedback[9])
        self.cur_el = (v1*100.0 + v2*10.0 + v3 + v4/10.0) - 360.0
        self.pv = ord(self.feedback[10])

    def format_set_cmd(self):
        #make sure cmd_az in range -180 to +540
        if   (self.cmd_az>540): self.cmd_az = 540
        elif (self.cmd_az < -180): self.cmd_az = -180
        #make sure cmd_el in range 0 to 180
        if   (self.cmd_el < 0): self.cmd_el = 0
        elif (self.cmd_el>180): self.cmd_el = 180
        #convert commanded az, el angles into strings
        cmd_az_str = str(int((float(self.cmd_az) + 360) * self.ph))
        cmd_el_str = str(int((float(self.cmd_el) + 360) * self.pv))
        #print target_az, len(target_az)
        #ensure strings are 4 characters long, pad with 0s as necessary
        if   len(cmd_az_str) == 1: cmd_az_str = '000' + cmd_az_str
        elif len(cmd_az_str) == 2: cmd_az_str = '00'  + cmd_az_str
        elif len(cmd_az_str) == 3: cmd_az_str = '0'   + cmd_az_str
        if   len(cmd_el_str) == 1: cmd_el_str = '000' + cmd_el_str
        elif len(cmd_el_str) == 2: cmd_el_str = '00'  + cmd_el_str
        elif len(cmd_el_str) == 3: cmd_el_str = '0'   + cmd_el_str
        #print target_az, len(str(target_az)), target_el, len(str(target_el))
        #update Set Command Message
        self.set_cmd[1] = cmd_az_str[0]
        self.set_cmd[2] = cmd_az_str[1]
        self.set_cmd[3] = cmd_az_str[2]
        self.set_cmd[4] = cmd_az_str[3]
        self.set_cmd[5] = self.ph
        self.set_cmd[6] = cmd_el_str[0]
        self.set_cmd[7] = cmd_el_str[1]
        self.set_cmd[8] = cmd_el_str[2]
        self.set_cmd[9] = cmd_el_str[3]
        self.set_cmd[10] = self.pv




class Tracker_Thread(threading.Thread):
    def __init__ (self, options):
        threading.Thread.__init__(self)
        self._stop = threading.Event()
        self.ip = options.ip
        self.port = options.port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP Socket
        self.cmd_az = 0.0       #Commanded Azimuth
        self.cmd_el = 0.0       #Commanded Elevation
        self.current_az = 0.0   #Current Azimuth
        self.current_el = 0.0   #Current Elevation
        self.az_tol = 0.0       #Azimuth Tolerance
        self.el_tol = 0.0       #Elevation Tolerance
        self.status = ""        #Antenna Pedestal Status

    def run(self):
        self.sock.connect((self.ip,self.port))
        while (not self._stop.isSet()):
            #data = self.sock.recv(1024)
            data = self.sock.makefile().readline(1024)
            data = data.strip('\n')
            data_list = data.split(',')
            if data_list[0] == '$':
                self.cmd_az     = float(data_list[1])   #Commanded Azimuth
                self.cmd_el     = float(data_list[2])   #Commanded Elevation
                self.current_az = float(data_list[3])   #Current Azimuth
                self.current_el = float(data_list[4])   #Current Elevation
                self.az_tol     = float(data_list[5])   #Azimuth Tolerance
                self.el_tol     = float(data_list[6])   #Elevation Tolerance
                self.status     = data_list[7].strip('\r')        #Antenna Pedestal Status
            #print self.cmd_az, self.cmd_el, self.current_az, self.current_el, self.az_tol, self.el_tol, self.status
        sys.exit()
        #time.sleep(0.25)

    
    def Write_Message(self, az, el):
        az_str = str(int(az))
        el_str = str(int(el))

        if len(az_str) == 1:
            az_str = "00" + az_str
        elif len(az_str) == 2:
            az_str = "0" + az_str
        
        if len(el_str) == 1:
            el_str = "00" + el_str
        elif len(el_str) == 2:
            el_str = "0" + el_str

        msg = "W" + az_str + " " + el_str
        #print msg
        self.sock.send(msg)

    def Write_Raw_Message(self, cmd):
        self.sock.send(cmd)

    def get_feedback(self):
        return self.cmd_az, self.cmd_el, self.current_az, self.current_el, self.az_tol, self.el_tol, self.status

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()
