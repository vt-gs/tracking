#!/usr/bin/env python
##################################################
# VTGS Tracking Protocol Class
# Version: 2.1
# Author: Zach Leffke
# DATE: July 2016
# Description: Class for interfacing VTGS Tracking Daemon
#   TCP Connection, CSV, etc.
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
    def __init__ (self, uid = None, ssid = None, cmd = None, az = None, el = None, valid = False):
        self.uid    = uid        
        self.ssid   = ssid
        self.cmd    = cmd
        self.az     = az
        self.el     = el
        self.valid  = valid

class MotionFrame(object):
    def __init__ (self, uid=None, ssid=None):
        #Header Fields
        self.uid     = uid       #User ID
        self.ssid    = ssid      #Subsystem ID
        self.type    = 'MOT'  #Command Type = MOTION
        self.cmd     = None   #
        self.az      = None
        self.el      = None
        self.az_rate = None
        self.el_rate = None
        self.valid   = False

class ManagementFrame(object):
    def __init__ (self, uid=None, ssid=None, cmd_type=None, valid = None):
        #Header Fields
        self.uid    = uid       #User ID
        self.ssid   = ssid      #Subsystem ID
        self.type   = cmd_type  #Command Type
        self.cmd    = None      #Valid Values: START, STOP, QUERY
        self.valid  = valid

class vtp(object):
    def __init__ (self, ip, port, uid = None, ssid = 'VUL', timeout = 1):
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
        self.uid        = uid
        #self.type       = 'MGMT'
        self.cmd        = 'QUERY'

        self.mgmt_fb_frame = ManagementFrame()  #Feedback Management Frame
        self.mot_fb_frame  = MotionFrame()      #Feedback Motion Frame

        self.tx_mgmt_frame = ManagementFrame(self.uid, self.ssid, 'MGMT')
        self.tx_mot_frame  = MotionFrame(self.uid, self.ssid)
        #self.tx_frame   = vtp_frame(ssid) #Transmit Frame to send to Tracking Daemon

        self.sock       = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP Socket
        self.sock.settimeout(self.timeout)
        self.connected = False

    ##### GENERAL FUNCTIONS #####
    def connect(self, ip, port, parent):
        self.sock       = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP Socket
        self.sock.settimeout(self.timeout)
        try:
            print self.utc_ts() + "Attempting to connect to Tracking Daemon" 
            self.sock.connect((self.ip,self.port))
            print self.utc_ts() + "Connection to Tracking Daemon Successful"
            time.sleep(0.05) 
            #self.get_daemon_state(True)
            self.connected = True
            return self.connected
        except socket.error as msg:
            print self.utc_ts() + "Exception Thrown: " + str(msg)
            print self.utc_ts() + "Failed to connect to Daemon" 
            self.connected = False
            return self.connected

    def get_connected(self):
        #return connection state
        return self.connected

    def disconnect(self):
        print self.utc_ts() + "Disconnecting from Tracking Daemon" 
        self.sock.close()
        self.connected = False
        return False

    def set_ssid(self, ssid):
        self.ssid = ssid
        self.tx_mgmt_frame.ssid = ssid
        self.tx_mot_frame.ssid = ssid

    def set_uid(self, uid):
        self.uid = uid
        self.tx_mgmt_frame.uid = uid
        self.tx_mot_frame.uid = uid

    def set_port(self, port):
        self.port = port

    def set_ip(self, ip):
        self.ip = ip

    def utc_ts(self):
        return str(date.utcnow()) + " UTC | VTP | "
    #***** END CLASS FUNCTIONS *****
    #
    #
    #
    ##### MOTION FRAME FUNCTIONS #####
    def set_stop(self):
        #stop md01 immediately
        self.tx_mot_frame.cmd = "STOP"
        if self.connected == True:
            try:
                msg = "{},{},{},{}".format( self.tx_mot_frame.uid, \
                                            self.tx_mot_frame.ssid, \
                                            self.tx_mot_frame.type, \
                                            self.tx_mot_frame.cmd)
                print self.utc_ts() + "Sent Message: " + msg
                self.sock.send(msg)
                self.feedback, addr = self.sock.recvfrom(1024)   
                self.mot_fb_frame.valid = self.validate_motion_feedback(self.feedback)
                self.connected = True
            except socket.error as msg:
                print self.utc_ts() + "Exception Thrown: " + str(msg) + " (" + str(self.timeout) + "s)"
                print self.utc_ts() + "Failed to receive feedback during \'set_stop\'..."
                print self.utc_ts() + "Setting connection status to \'False\'..."
                self.connected = False
        else:
            print self.utc_ts() + "Not Connected to Daemon..."

        return self.connected
        #return self.mot_fb_frame.valid, self.mot_fb_frame.az, self.mot_fb_frame.el, self.mot_fb_frame.az_rate, self.mot_fb_frame.el_rate


    def set_position(self, az, el, verbosity):
        #set azimuth and elevation of md01
        self.tx_mot_frame.cmd = "SET"
        self.tx_mot_frame.az,self.tx_mot_frame.el = self.verify_set_angles(az,el)
        if self.connected == True:
            try:
                msg = "{},{},{},{},{},{}".format(   self.tx_mot_frame.uid, \
                                                    self.tx_mot_frame.ssid, \
                                                    self.tx_mot_frame.type, \
                                                    self.tx_mot_frame.cmd, \
                                                    self.tx_mot_frame.az, \
                                                    self.tx_mot_frame.el)
                if verbosity: print self.utc_ts() + "Sent Message: " + msg
                self.sock.send(msg)
                self.feedback, addr = self.sock.recvfrom(1024)   
                self.mot_fb_frame.valid = self.validate_motion_feedback(self.feedback)
                self.connected = True
            except socket.error as msg:
                print self.utc_ts() + "Exception Thrown: " + str(msg)
                print self.utc_ts() + "Failed to receive feedback during Set Position..."
                print self.utc_ts() + "Setting connection status to \'False\'..."
                self.connected = False

            return self.connected, self.mot_fb_frame.valid, self.mot_fb_frame.az, self.mot_fb_frame.el, self.mot_fb_frame.az_rate, self.mot_fb_frame.el_rate
        else:
            print self.utc_ts() + "Not Connected to Daemon..."
            return self.connected

    def verify_set_angles(self, cmd_az, cmd_el):
        #make sure cmd_az in range -180 to +540
        if   (cmd_az>540): cmd_az = 540
        elif (cmd_az < -180): cmd_az = -180
        #make sure cmd_el in range 0 to 180
        if   (cmd_el < 0): cmd_el = 0
        elif (cmd_el>180): cmd_el = 180
        return cmd_az, cmd_el

    def get_motion_feedback(self, verbosity):
        #msg = ""
        #msg += self.uid + ','
        #msg += self.ssid + ','
        #msg += 'MOT,'
        #msg += 'GET'
        self.tx_mot_frame.cmd = "GET"
        if self.connected == True:
            try:
                msg = "{},{},{},{}".format(   self.tx_mot_frame.uid, \
                                                    self.tx_mot_frame.ssid, \
                                                    self.tx_mot_frame.type, \
                                                    self.tx_mot_frame.cmd)    
                if verbosity: print self.utc_ts() + "Sent Message: " + msg
                self.sock.send(msg)
                self.feedback, addr = self.sock.recvfrom(1024)   
                self.mot_fb_frame.valid = self.validate_motion_feedback(self.feedback)
                self.connected = True
            except socket.error as msg:
                print self.utc_ts() + "Exception Thrown: " + str(msg)
                print self.utc_ts() + "Failed to receive feedback during \'get_motion_feedback\'"
                print self.utc_ts() + "Setting connection state to False..."
                self.connected = False
            return self.connected, self.mot_fb_frame.valid, self.mot_fb_frame.az, self.mot_fb_frame.el, self.mot_fb_frame.az_rate, self.mot_fb_frame.el_rate
        else:
            print self.utc_ts() + "Not Connected to Daemon..."
            return self.connected

    def validate_motion_feedback(self, feedback):
        fields = feedback.strip().split(",")
        #Expected to receive a managment frame
        if (len(fields) == 8):
            try:
                self.mot_fb_frame.uid  = fields[0].strip()
                self.mot_fb_frame.ssid = fields[1].strip()
                self.mot_fb_frame.type = fields[2].strip()
                self.mot_fb_frame.cmd  = fields[3].strip()
                #print self.mgmt_fb_frame.uid,self.mgmt_fb_frame.ssid,self.mgmt_fb_frame.type,self.mgmt_fb_frame.cmd
            except ValueError:
                print self.utc_ts() + "Invalid data types in management frame feedback"
                return False
        else: 
            print self.utc_ts() + "Invalid number of fields in management frame feedback: ", len(fields) 
            return False

        # Header Check
        if self.mot_fb_frame.uid != self.uid:
            print "{:s}Invalid feedback USERID, expected: {:s}, received: {:s}".format(self.utc_ts(), self.uid, self.mot_fb_frame.uid)
            return False
            
        if self.mot_fb_frame.ssid != self.ssid:
            print "{:s}Invalid feedback SSID, expected: {:s}, received: {:s}".format(self.utc_ts(), self.ssid, self.mot_fb_frame.ssid)
            return False

        if self.mot_fb_frame.type != 'MOT':
            print "{:s}Invalid feedback TYPE, expected: {:s}, received: {:s}".format(self.utc_ts(), 'MOT', self.mot_fb_frame.type)
            return False

        if self.mot_fb_frame.cmd != 'STATE':
            print "{:s}Invalid feedback CMD, expected: {:s}, received: {:s}".format(self.utc_ts(), 'STATE', self.mot_fb_frame.type)
            return False

        try:
            self.mot_fb_frame.az        = float(fields[4].strip())
            self.mot_fb_frame.el        = float(fields[5].strip())
            self.mot_fb_frame.az_rate   = float(fields[6].strip())
            self.mot_fb_frame.el_rate   = float(fields[7].strip())
            #print self.mgmt_fb_frame.uid,self.mgmt_fb_frame.ssid,self.mgmt_fb_frame.type,self.mgmt_fb_frame.cmd
        except ValueError:
            print self.utc_ts() + "Invalid data types in motion frame feedback"
            return False

        return True

    #***** END MOTION FRAME FUNCTIONS *****
    #
    #
    #
    ##### MANAGEMENT FRAME FUNCTIONS #####
    def get_daemon_state(self, verbosity=False):
        #msg = ""
        #msg += self.uid + ','
        #msg += self.ssid + ','
        #msg += 'MGMT,'
        #msg += 'QUERY'
        #self.tx_mgmt_frame.type = 'MGMT'
        self.tx_mgmt_frame.cmd = 'QUERY'
        if self.connected == True:
            try:        
                msg = "{},{},{},{}".format(   self.tx_mgmt_frame.uid, \
                                                    self.tx_mgmt_frame.ssid, \
                                                    self.tx_mgmt_frame.type, \
                                                    self.tx_mgmt_frame.cmd)  
                if verbosity: print self.utc_ts() + "Sent Message: " + msg
                self.sock.send(msg)
                self.feedback, addr = self.sock.recvfrom(1024)   
                self.mgmt_fb_frame.valid = self.validate_management_feedback(self.feedback)
                self.connected = True
            except socket.error as msg:
                print self.utc_ts() + "Exception Thrown: " + str(msg)
                print self.utc_ts() + "Failed to receive feedback during \'get_daemon_state\'"
                print self.utc_ts() + "Setting connection state to False..."
                self.connected = False
            return self.connected, self.mgmt_fb_frame.valid, self.mgmt_fb_frame.cmd
        else:
            if verbosity: print self.utc_ts() + "Not Connected to Daemon..."
            return self.connected, 'INVALID', 'NONE'

    def set_session_start(self):
        msg = ""
        msg += self.uid + ','
        msg += self.ssid + ','
        msg += 'MGMT,'
        msg += 'START'
        try:        
            print self.utc_ts() + "Sent Message: " + msg
            self.sock.send(msg)
            self.feedback, addr = self.sock.recvfrom(1024)   
            self.mgmt_fb_frame.valid = self.validate_management_feedback(self.feedback)
        except socket.error as msg:
            print self.utc_ts() + "Exception Thrown: " + str(msg)
            print self.utc_ts() + "Failed to receive feedback during \'set_session_start\'"
        return self.mgmt_fb_frame.valid, self.mgmt_fb_frame.cmd

    def set_session_stop(self):
        msg = ""
        msg += self.uid + ','
        msg += self.ssid + ','
        msg += 'MGMT,'
        msg += 'STOP'
        try:        
            print self.utc_ts() + "Sent Message: " + msg
            self.sock.send(msg)
            self.feedback, addr = self.sock.recvfrom(1024)   
            self.mgmt_fb_frame.valid = self.validate_management_feedback(self.feedback)
        except socket.error as msg:
            print self.utc_ts() + "Exception Thrown: " + str(msg)
            print self.utc_ts() + "Failed to receive feedback during \'set_session_stop\'"
        return self.mgmt_fb_frame.valid, self.mgmt_fb_frame.cmd

    def validate_management_feedback(self, feedback):
        fields = feedback.strip().split(",")
        #Expected to receive a managment frame
        if (len(fields) == 4):
            try:
                self.mgmt_fb_frame.uid  = fields[0].strip()
                self.mgmt_fb_frame.ssid = fields[1].strip()
                self.mgmt_fb_frame.type = fields[2].strip()
                self.mgmt_fb_frame.cmd  = fields[3].strip()
                #print self.mgmt_fb_frame.uid,self.mgmt_fb_frame.ssid,self.mgmt_fb_frame.type,self.mgmt_fb_frame.cmd
            except ValueError:
                print self.utc_ts() + "Invalid data types in management frame feedback"
                return False
        else: 
            print self.utc_ts() + "Invalid number of fields in management frame feedback: ", len(fields) 
            return False
        
        if self.mgmt_fb_frame.uid != self.uid:
            print "{:s}Invalid feedback USERID, expected: {:s}, received: {:s}".format(self.utc_ts(), self.uid, self.mgmt_fb_frame.uid)
            return False
            
        if self.mgmt_fb_frame.ssid != self.ssid:
            print "{:s}Invalid feedback SSID, expected: {:s}, received: {:s}".format(self.utc_ts(), self.ssid, self.mgmt_fb_frame.ssid)
            return False

        if self.mgmt_fb_frame.type != 'MGMT':
            print "{:s}Invalid feedback TYPE, expected: {:s}, received: {:s}".format(self.utc_ts(), 'MGMT', self.mgmt_fb_frame.type)
            return False

        return True
    #***** END MANAGEMENT FRAME FUNCTIONS *****


