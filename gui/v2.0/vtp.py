#!/usr/bin/env python
##################################################
# VTGS Tracking Protocol Class
# Version: 2.0
# Author: Zach Leffke
# Description: Class for interfacing VTGS Tracking Daemon
##################################################
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

class vtp_frame(object):
    def __init__ (self, ssid = None, cmd = None, az = None, el = None, valid = False):
        self.ssid   = ssid
        self.cmd    = cmd
        self.az     = az
        self.el     = el
        self.valid  = valid

class vtp(object):
    def __init__ (self, ip, port, ssid = 'VUL', timeout = 1):
        self.ip         = ip        #IP Address of MD01 Controller
        self.port       = port      #Port number of MD01 Controller
        self.timeout    = timeout   #Socket Timeout interval, default = 1.0 seconds

        self.cmd_az     = 180.0     #Commanded Azimuth, used in Set Position Command
        self.cmd_el     = 0         #Commanded Elevation, used in Set Position command
        self.cur_az     = 0         #  Current Azimuth, in degrees, from feedback
        self.cur_el     = 0         #Current Elevation, in degrees, from feedback
        self.az_rate    = 0         #  Azimuth Rate, degrees/second, from feedback
        self.el_rate    = 0         #Elevation Rate, degrees/second, from feedback

        self.feedback   = ''        #Feedback data from socket
        self.stop_cmd   = ''
        self.status_cmd = ''
        self.set_cmd    = ''

        self.ssid       = ssid
        self.cmd        = ''

        self.fb_frame   = vtp_frame() #Feedback Frame
        self.tx_frame   = vtp_frame(ssid) #Transmit Frame to send to Tracking Daemon

        self.sock       = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP Socket
        self.sock.settimeout(self.timeout)

    def set_ssid(self, ssid):
        self.ssid = ssid
        self.tx_frame.ssid = ssid

    def utc_ts(self):
        return str(date.utcnow()) + " UTC | "

    def get_status(self):
        try:        
            msg = self.ssid + " GET"
            #print self.utc_ts() + "VTP | Sent Message: " + msg
            self.sock.sendto(msg, (self.ip, self.port))
            self.feedback, addr = self.sock.recvfrom(1024)   
            #print self.feedback  
            self.fb_frame.valid = self.Validate_Feedback()  
            #self.feedback = self.recv_data()          
        except socket.error as msg:
            print self.utc_ts() + "VTP | Exception Thrown: " + str(msg)
            print self.utc_ts() + "VTP |Failed to receive feedback during Get Status..."
            #continue
            #self.sock.close()
            #sys.exit()
        #if self.fb_frame.valid == True: self.Parse_Feedback()  
        return self.fb_frame.valid, self.cur_az, self.cur_el 

    def set_stop(self):
        #stop md01 immediately
        try:
            msg = self.ssid + " STOP"
            print self.utc_ts() + "VTP | Sent Message: " + msg
            self.sock.sendto(msg, (self.ip, self.port))
            self.feedback, addr = self.sock.recvfrom(1024)   
            self.fb_frame.valid = self.Validate_Feedback()          
        except socket.error as msg:
            print self.utc_ts() + "VTP | Exception Thrown: " + str(msg) + " (" + str(self.timeout) + "s)"
            print self.utc_ts() + "VTP | Failed to receive feedback during Set Stop..."
            #continue
            #self.sock.close()
            #sys.exit()
        return self.fb_frame.valid, self.cur_az, self.cur_el  #return 0 good status, feedback az/el 

    def set_position(self, az, el):
        #set azimuth and elevation of md01
        self.cmd_az = az
        self.cmd_el = el
        self.tx_frame.cmd = "SET"
        self.format_set_cmd()
        try:
            #msg = self.ssid + " " + self.cmd + " " + self.cmd_az + " " + self.cmd_el
            msg = "{} {} {} {}".format(self.tx_frame.ssid, self.tx_frame.cmd, round(self.cmd_az,1), round(self.cmd_el,1))
            print self.utc_ts() + "VTP | Sent Message: " + msg
            self.sock.sendto(msg, (self.ip, self.port))
            self.feedback, addr = self.sock.recvfrom(1024)   
            self.fb_frame.valid = self.Validate_Feedback() 
        except socket.error as msg:
            print self.utc_ts() + "VTP | Exception Thrown: " + str(msg)
            print self.utc_ts() + "VTP | Failed to receive feedback during Set Position..."
            #continue
            #self.sock.close()
            #sys.exit()

    def Validate_Feedback(self):
        fields = self.feedback.split(" ")
        #print fields
        #Check number of fields        
        if (len(fields) == 4):
            try:
                self.fb_frame.ssid = fields[0].strip('\n')
                self.fb_frame.cmd  = fields[1].strip('\n')
            except ValueError:
                print self.utc_ts() + "VTP | Invalid Command Data Types"
                return False
        else: 
            print self.utc_ts() + "VTP | Invalid number of fields in command: ", len(fields) 
            return False
        #Validate Subsystem ID
        if ((self.fb_frame.ssid != 'VUL') and (self.fb_frame.ssid != '3M0') and (self.fb_frame.ssid != '4M5') and (self.fb_frame.ssid != 'WX')):
            print self.utc_ts() + "VTP | Invalid Subsystem ID Type: ", self.req.ssid
            return False
        #Validate QUERY Command Type
        if (self.fb_frame.cmd != 'QUERY'):
            print self.utc_ts() + "VTP | Invalid Command Type: ", self.fb_frame.cmd
            return False
        else:
            try:
                self.fb_frame.az = float(fields[2].strip('\n'))
                self.fb_frame.el = float(fields[3].strip('\n'))
                self.cur_az = self.fb_frame.az
                self.cur_el = self.fb_frame.el
            except ValueError:
                print self.utc_ts() + "VTP | Invalid Az/El Data Types"
                return False
        #print self.fb_frame.ssid, self.fb_frame.cmd, self.fb_frame.az, self.fb_frame.el
        return True

    def format_set_cmd(self):
        #make sure cmd_az in range -180 to +540
        if   (self.cmd_az>540): self.cmd_az = 540
        elif (self.cmd_az < -180): self.cmd_az = -180
        #make sure cmd_el in range 0 to 180
        if   (self.cmd_el < 0): self.cmd_el = 0
        elif (self.cmd_el>180): self.cmd_el = 180

        self.tx_frame.az = self.cmd_az
        self.tx_frame.el = self.cmd_el

