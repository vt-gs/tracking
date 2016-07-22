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

from datetime import datetime as date

class MotionFrame(object):
    def __init__ (self, uid=None, ssid=None, cmd_type=None):
        #Header Fields
        self.uid     = uid       #User ID
        self.ssid    = ssid      #Subsystem ID
        self.type    = cmd_type  #Command Type
        self.cmd     = None   #
        self.az      = None
        self.el      = None
        self.az_rate = None
        self.el_rate = None

class ManagementFrame(object):
    def __init__ (self, uid=None, ssid=None, cmd_type=None):
        #Header Fields
        self.uid    = uid       #User ID
        self.ssid   = ssid      #Subsystem ID
        self.type   = cmd_type  #Command Type
        self.cmd    = None      #Valid Values: START, STOP, QUERY

class ServerThread(threading.Thread):
    def __init__ (self, ssid, ip, port):
        threading.Thread.__init__(self)
        self._stop      = threading.Event()
        self.ssid       = ssid
        self.ip         = ip
        self.port       = port

        #Setup Socket
        #self.sock      = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP Socket
        self.sock       = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP Socket
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #To allow socket reuse
        self.sock.settimeout(1)

        self.user_con   = False
        self.frame      = None
        self.valid      = 0     # 0=invalid, 1=Management Frame, 2=Antenna Frame

        self.callback = None # callback to Daemon Main Thread

        self.init_thread()

    def init_thread(self):
        pass

    def run(self):
        print self.utc_ts() + self.ssid + " Server Thread Started..."
        self.sock.bind((self.ip, self.port))
        self.sock.listen(1)
        while (not self._stop.isSet()): 
            try:
                if self.user_con == False:
                    self.conn, self.addr = self.sock.accept()#Blocking
                    print self.utc_ts() + "User connected from: " + str(self.addr)
                    #self.user_con = True
                    self.set_user_con_status(True)
                elif self.user_con == True:
                    data = self.conn.recvfrom(1024)[0]
                    if data:
                        data = data.strip()
                        print self.utc_ts() + "User Message: " + str(data)
                        #self.valid = self.check_frame(data)
                        if self.check_frame(data): #True if fully validated frame
                            #Valid FRAME with all checks complete at this point
                            if self.frame.type == 'MOT': #Process Motion Frame
                                self.process_motion()
                            elif self.frame.type == 'MGMT': #Process Management Frame
                                self.process_management()
                        else:
                            self.conn.sendall('INVALID,' + data + '\n')
                    else:
                        print self.utc_ts() + "User disconnected from: " + str(self.addr)  
                        #self.user_con = False                      
                        self.set_user_con_status(False)

            except Exception as e:
                #print e
                pass

    #### FUNCTIONS CALLED BY MAIN THREAD ####
    def send_management_feedback(self, daemon_state):
        msg = ""
        msg += self.frame.uid + ','
        msg += self.frame.ssid + ','
        msg += self.frame.type + ','
        msg += daemon_state + '\n'
        self.conn.sendall(msg)

    def send_motion_feedback(self, az,el,az_rate,el_rate):
        msg = ""
        msg += self.frame.uid + ','
        msg += self.frame.ssid + ','
        msg += self.frame.type + ','
        msg += 'STATE,'
        msg += '{:3.1f},{:3.1f},{:1.3f},{:1.3f}\n'.format(az,el,az_rate,el_rate)
        self.conn.sendall(msg)

    #### MAIN THREAD FUNCTION CALLS ####
    def set_user_con_status(self, status):
        #sets user connection status
        self.user_con = status
        self.callback.set_user_con_status(self.user_con)

    def process_motion(self):
        self.callback.motion_frame_received(self, self.frame)

    def process_management(self):
        self.callback.management_frame_received(self, self.frame)

    def set_callback(self, callback):
        #callback function leads to main thread.
        self.callback = callback


    #### LOCAL FUNCTION CALLS ####
    def check_frame(self, data):
        #validates header field of received frame.
        uid     = None
        ssid    = None
        frame_type = None
        try: #look for generic exception
            fields = data.split(",") 
            msg = 'INVALID: '
            if len(fields) < 4:
                print self.utc_ts() + 'Invalid number of fields in frame: ', len(fields)  
                return False
            else:
                #validate USERID, this will always be accepted and will probably never be excepted
                try:
                    uid = str(fields[0])  #typecast first field to string and assign to request object
                except:
                    print self.utc_ts() + 'Could not assign User ID: ', fields[0]
                    #self.conn.sendall(msg + data)
                    return False

                #Validate SSID
                ssid = str(fields[1]).strip().upper()  #typecast to string, remove whitespace, force to uppercase
                if ssid != self.ssid:
                    print '{:s}Invalid SSID: \'{:s}\' from user \'{:s}\''.format(self.utc_ts(), ssid, self.req.uid)
                    print self.utc_ts() + "This is the VUL Tracking Daemon"
                    #self.conn.sendall(msg+data)
                    return False
                #else:
                #    self.req.ssid = ssid

                #Validate frame TYPE
                frame_type = str(fields[2]).strip().upper()
                if ((frame_type != 'MGMT') and (frame_type != 'MOT')):
                    print '{:s}Invalid Frame Type: \'{:s}\' from user \'{:s}\''.format(self.utc_ts(), frame_type, self.req.uid)
                    print self.utc_ts() + "Valid Frame Types: \'MOT\'=Motion Frame, \'MGMT\'=Management Frame"
                    #self.conn.sendall(msg+data)
                    return False
                #else:
                #    self.req.type = frame_type

        except Exception as e:
            print '{:s}Unknown Exception: \'{:s}\''.format(self.utc_ts(), e)
            #self.conn.sendall(msg+data)
            return False

        del self.frame
        #self.frame = None
        
        if frame_type == 'MGMT':
            self.frame = ManagementFrame(uid, ssid, frame_type)
            return self.check_management_frame(fields)
        elif frame_type == 'MOT':
            self.frame = MotionFrame(uid, ssid, frame_type)
            return self.check_motion_frame(fields)
        else:
            return False        
    
    def check_motion_frame(self, fields):
        cmd = None
        az  = None
        el  = None
        try:
            cmd = fields[3].strip().upper()
            if ((cmd != 'SET') and (cmd != 'GET') and (cmd != 'STOP')): 
                print '{:s}Invalid Motion Frame Command: \'{:s}\' from user \'{:s}\''.format(self.utc_ts(), cmd, self.frame.uid)
                print self.utc_ts() + "Valid MOT Commands: \'SET\', \'GET\', \'STOP\'"
                return False

            if cmd == 'SET':  #get the Commanded az/el angles
                if len(fields) < 6:
                    print '{:s}Invalid number of fields in \'SET\' Command: \'{:s}\' from user \'{:s}\''.format(self.utc_ts(), str(len(fields)), self.frame.uid)
                try:
                    az = float(fields[4].strip())
                    el = float(fields[5].strip())
                except:
                    print '{:s}Invalid data types in az/el fields of \'SET\' Command from user \'{:s}\''.format(self.utc_ts(), self.frame.uid)

        except Exception as e:
            print '{:s}Unknown Exception: \'{:s}\''.format(self.utc_ts(), e)
            return False
        
        self.frame.cmd = cmd
        self.frame.az = az
        self.frame.el = el
        return True
    

    def check_management_frame(self, fields):
        #Check fourth field for valid command
        cmd = None
        try:
            cmd = fields[3].strip().upper()
            if ((cmd != 'START') and (cmd != 'STOP') and (cmd != 'QUERY')): 
                print '{:s}Invalid Management Frame Command: \'{:s}\' from user \'{:s}\''.format(self.utc_ts(), cmd, self.frame.uid)
                print self.utc_ts() + "Valid MGMT Commands: \'START\', \'STOP\', \'QUERY\'"
                return False
            
        except Exception as e:
            print '{:s}Unknown Exception: \'{:s}\''.format(self.utc_ts(), e)
            return False
        
        self.frame.cmd = cmd
        return True
            
    def utc_ts(self):
        return str(date.utcnow()) + " UTC | SERV | "

    def stop(self):
        self._stop.set()
        sys.quit()

    def stopped(self):
        return self._stop.isSet()

    






###### OLD FUNCTIONS ########################33
    def check_request(self, data):
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


    def process_request(self, data, addr):
        if   self.req.ssid == self.ssid: #VHF/UHF/L-Band subsystem ID
            self.Process_Command(self.md01_thread, data, addr)
        else:
            print self.utc_ts() + "This is the VUL Controller"

    def process_command(self, thr, data, addr):
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

    def send_feedback(self,thr, az, el, data, addr):
        msg = thr.ssid + " QUERY " + str(az) + " " + str(el) + "\n"
        self.sock.sendto(msg, addr)


    


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




