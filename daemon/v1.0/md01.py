#!/usr/bin/env python
#########################################
#   Title: MD01 Controller Class        #
# Project: VTGS Tracking Daemon         #
# Version: 1.0                          #
#    Date: Dec 1, 2015                  #
#  Author: Zach Leffke, KJ4QLP          #
# Comment: This is the initial version  # 
#          of the MD-01 interface and   #
#          only contains functionality  #
#          for the Set, Query, and Stop #
#          commands.                    #
#########################################
import socket
import os
import string
import sys
import time
import curses
import threading
from binascii import *
from datetime import datetime as date
from optparse import OptionParser

class md01(object):
    def __init__ (self, ip, port, timeout = 1.0, retries = 2):
        self.ip         = ip        #IP Address of MD01 Controller
        self.port       = port      #Port number of MD01 Controller
        self.timeout    = timeout   #Socket Timeout interval, default = 1.0 seconds
        self.connected  = False
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

    def getTimeStampGMT(self):
        return str(date.utcnow()) + " GMT | "

    def connect(self):
        #connect to md01 controller
        self.sock       = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP Socket
        self.sock.settimeout(self.timeout)   #set socket timeout
        print self.getTimeStampGMT() + 'MD01 |  Attempting to connect to MD01 Controller: ' + str(self.ip) + ' ' + str(self.port)
        try:
            self.sock.connect((self.ip, self.port))
            self.connected = True
            return self.connected
            #upon connection, get status to determine current antenna position
            #self.get_status()
        except socket.error as msg:
            print "Exception Thrown: " + str(msg) + " (" + str(self.timeout) + "s)"
            print "Unable to connect to MD01 at IP: " + str(self.ip) + ", Port: " + str(self.port)  
            print "Terminating Program..."
            sys.exit()

    def disconnect(self):
        #disconnect from md01 controller
        print self.getTimeStampGMT() + "MD01 |  Attempting to disconnect from MD01 Controller"
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
        self.connected = False
        print self.getTimeStampGMT() + "MD01 |  Successfully disconnected from MD01 Controller"
    
    def get_status(self):
        #get azimuth and elevation feedback from md01
        if self.connected == False:
            self.printNotConnected('Get MD01 Status')
            return -1,0,0 #return -1 bad status, 0 for az, 0 for el
        else:
            try:
                self.sock.send(self.status_cmd) 
                self.feedback = self.recv_data()          
            except socket.error as msg:
                print "Exception Thrown: " + str(msg) + " (" + str(self.timeout) + "s)"
                print "Closing socket, Terminating program...."
                self.sock.close()
                sys.exit()
            self.convert_feedback()  
            return 0, self.cur_az, self.cur_el #return 0 good status, feedback az/el 

    def set_stop(self):
        #stop md01 immediately
        if self.connected == False:
            self.printNotConnected('Set Stop')
            return -1, 0, 0
        else:
            try:
                self.sock.send(self.stop_cmd) 
                self.feedback = self.recv_data()          
            except socket.error as msg:
                print "Exception Thrown: " + str(msg) + " (" + str(self.timeout) + "s)"
                print "Closing socket, Terminating program...."
                self.sock.close()
                sys.exit()
            self.convert_feedback()
            return 0, self.cur_az, self.cur_el  #return 0 good status, feedback az/el 

    def set_position(self, az, el):
        #set azimuth and elevation of md01
        self.cmd_az = az
        self.cmd_el = el
        self.format_set_cmd()
        if self.connected == False:
            self.printNotConnected('Set Position')
            return -1
        else:
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
        #print hexlify(feedback)
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

    def printNotConnected(self, msg):
        print self.getTimeStampGMT() + "MD01 |  Cannot " + msg + " until connected to MD01 Controller."


