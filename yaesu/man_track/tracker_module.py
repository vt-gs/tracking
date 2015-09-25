#!/usr/bin/env python
import socket
import os
import string
import sys
import time
import curses
import threading
from optparse import OptionParser

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
