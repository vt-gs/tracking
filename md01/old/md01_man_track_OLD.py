#!/usr/bin/env python
import socket
import os
import string
import sys
import time
import curses
import threading
from optparse import OptionParser
from binascii import *
#from md01 import *
#from curses_display import *

class md01(object):
    def __init__ (self, options):
        self.md01_ip = options.ip       #IP Address of MD01 Controller
        self.md01_port = options.port   #Port number of MD01 Controller
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP Socket
        self.cmd_az = 0                 #Commanded Azimuth, used in Set Position Command
        self.cmd_el = 0                 #Commanded Elevation, used in Set Position command
        self.cur_az = 0                 #  Current Azimuth, in degrees, from feedback
        self.cur_el = 0                 #Current Elevation, in degrees, from feedback
        self.ph = 10                    #  Azimuth Resolution, in pulses per degree, from feedback, default = 10
        self.pv = 10                    #Elevation Resolution, in pulses per degree, from feedback, default = 10
        self.feedback = ''              #Feedback data from socket
        self.stop_cmd = bytearray()     #Stop Command Message
        self.status_cmd = bytearray()   #Status Command Message
        self.set_cmd = bytearray()      #Set Command Message
        for x in [0x57,0,0,0,0,0,0,0,0,0,0,0x0F,0x20]: self.stop_cmd.append(x)
        for x in [0x57,0,0,0,0,0,0,0,0,0,0,0x1F,0x20]: self.status_cmd.append(x)
        for x in [0x57,0,0,0,0,0x0a,0,0,0,0,0x0a,0x2F,0x20]: self.set_cmd.append(x) #PH=PV=0x0a, 0x0a = 10, BIG-RAS/HR is 10 pulses per degree

    def connect(self):
        #connect to md01 controller
        self.sock.settimeout(1.0)
        self.sock.connect((self.ip, self.port))
        self.get_status()

    def disconnect(self):
        #disconnect from md01 controller
        self.sock.close()
    
    def get_status(self):
        #get azimuth and elevation feedback from md01
        try:
            self.sock.send(status_cmd) 
            self.recv_data()          
        except socket.error as msg:
            print msg
            self.sock.close()
            sys.exit()
        self.convert_feedback()    

    def set_stop(self):
        #stop md01 immediately
        try:
            self.sock.send(stop_cmd) 
            self.recv_data()          
        except socket.error as msg:
            print msg
            self.sock.close()
            sys.exit()
        self.convert_feedback()   

    def set_az_el(self, az, el):
        #set azimuth and elevation of md01
        self.cmd_az = az
        self.cmd_el = el
        self.format_set_cmd()
        try:
            self.sock.send(set_cmd) 
        except socket.error as msg:
            print msg
            self.sock.close()
            sys.exit()

    def recv_data(self):
        #receive socket data
        self.feedback = ''
        while True:
            c = self.sock.recv(1)
            if hexlify(c) == '20':
                self.feedback += c
                break
            else:
                self.feedback += c

    def convert_feedback(self):
        h1 = self.feedback[1]
        h2 = self.feedback[2]
        h3 = self.feedback[3]
        h4 = self.feedback[4]
        self.cur_az = ord(h1)*100.0 + ord(h2)*10.0 + ord(h3)*10.0 + ord(h4)/10.0 - 360.0
        self.ph = ord(self.feedback[5])

        v1 = self.feedback[1]
        v2 = self.feedback[2]
        v3 = self.feedback[3]
        v4 = self.feedback[4]
        self.cur_el = ord(v1)*100.0 + ord(v2)*10.0 + ord(v3)*10.0 + ord(v4)/10.0 - 360.0
        self.pv = ord(self.feedback[5])

    def format_set_cmd(self):
        #make sure cmd_az in range 0 to 360
        if   (self.cmd_az>360): self.cmd_az = self.cmd_az - 360
        elif (self.cmd_az < 0): self.cmd_az = self.cmd_az + 360
        #make sure cmd_el in range 0 to 180
        if   (self.cmd_el < 0): self.cmd_el = 0
        elif (self.cmd_az>180): self.cmd_el = 180
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
        self.set_cmd[5] = ph
        self.set_cmd[6] = cmd_el_str[0]
        self.set_cmd[7] = cmd_el_str[1]
        self.set_cmd[8] = cmd_el_str[2]
        self.set_cmd[9] = cmd_el_str[3]
        self.set_cmd[10] = pv

def recv_data(sock):
    data = ''
    while True:
        c = sock.recv(1)

        if hexlify(c) == '20':
            data += c
            break
        else:
            data += c
    return data

def convert_data(data):
    h1 = data[1]
    h2 = data[2]
    h3 = data[3]
    h4 = data[4]
    az = ord(h1)*100.0 + ord(h2)*10.0 + ord(h3)*10.0 + ord(h4)/10.0 - 360.0
    ph = ord(data[5])
    v1 = data[6]
    v2 = data[7]
    v3 = data[8]
    v4 = data[9]
    el = ord(v1)*100.0 + ord(v2)*10.0 + ord(v3)*10.0 + ord(v4)/10.0 - 360.0
    pv = ord(data[10])
    return az, el, ph, pv

if __name__ == '__main__':
	
    #--------START Command Line option parser------------------------------------------------
    usage = "usage: %prog -a <Server Address> -p <Server Port> "
    parser = OptionParser(usage = usage)
    s_help = "IP address of tracker, Default: 192.168.42.21"
    p_help = "TCP port number of tracker, Default: 2000"
    parser.add_option("-a", dest = "ip"  , action = "store", type = "string", default = "192.168.42.21", help = s_help)
    parser.add_option("-p", dest = "port", action = "store", type = "int"   , default = "2000"         , help = p_help)
    (options, args) = parser.parse_args()
    #--------END Command Line option parser-------------------------------------------------

    #tt = Tracker_Thread(options)
    #dt = Display_Thread(options, tt)
    #tt.daemon = True
    #dt.daemon = True
    #tt.start()
    #dt.run()
    
    stop_cmd = bytearray() 
    status_cmd = bytearray()
    set_cmd = bytearray()
    az = 0
    el = 0
    pv = 0
    ph = 0
    for x in [0x57,0,0,0,0,0,0,0,0,0,0,0x0F,0x20]: stop_cmd.append(x)
    for x in [0x57,0,0,0,0,0,0,0,0,0,0,0x1F,0x20]: status_cmd.append(x)
    for x in [0x57,0,0,0,0,2,0,0,0,0,2,0x2F,0x20]: set_cmd.append(x) #PH=PV=0x0a, 0x0a = 10, BIG-RAS/HR is 10 pulses per degree
    
    
    #for i in range(len(status_cmd)): print hexlify(str(status_cmd[i]))
    #print hexlify(status_cmd)
    #status_cmd.insert(11,0x0F)
    #status_cmd.pop(12)
    #print hexlify(status_cmd)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP Socket
    sock.settimeout(1.0)

    try:
        sock.connect((options.ip, options.port))
    except socket.error as msg:
        print msg
        sys.exit()

    try:
        sock.send(stop_cmd) 
        data = recv_data(sock)          
    except socket.error as msg:
        print msg
        sock.close()
        sys.exit()            
    print (hexlify(data)), len(data)
    az, el, ph, pv = convert_data(data)
    print az, el, ph, pv
    x = ""
    while True:
        x = raw_input('Send command: 1=stop, 2=status, 3=set: ')
        if (x == '1'):
            try:
                sock.send(stop_cmd) 
                data = recv_data(sock)          
            except socket.error as msg:
                print msg
                sock.close()
                sys.exit()            
            print (hexlify(data)), len(data)
            az, el, ph, pv = convert_data(data)
            print az, el
        elif (x == '2'):
            try:
                sock.send(status_cmd) 
                data = recv_data(sock)          
            except socket.error as msg:
                print msg
                sock.close()
                sys.exit()            
            print (hexlify(data)), len(data)
            az, el, pv, ph = convert_data(data)
            print az, el, ph, pv
        elif (x == '3'):
            target_az = raw_input('  Enter Azimuth: ')
            target_el = raw_input('Enter Elevation: ')
            target_az = str(int((float(target_az) + 360) * ph))
            target_el = str(int((float(target_el) + 360) * pv))
            print target_az, len(target_az)
            
            if   len(target_az) == 1: target_az = '000' + str(target_az)
            elif len(target_az) == 2: target_az = '00' + str(target_az)
            elif len(target_az) == 3: target_az = '0' + str(target_az)
            if   len(target_el) == 1: target_el = '000' + str(target_el)
            elif len(target_el) == 2: target_el = '00' + str(target_el)
            elif len(target_el) == 3: target_el = '0' + str(target_el)
            

            print target_az, len(str(target_az)), target_el, len(str(target_el))
            set_cmd[1] = target_az[0]
            set_cmd[2] = target_az[1]
            set_cmd[3] = target_az[2]
            set_cmd[4] = target_az[3]
            set_cmd[5] = ph
            set_cmd[6] = target_el[0]
            set_cmd[7] = target_el[1]
            set_cmd[8] = target_el[2]
            set_cmd[9] = target_el[3]
            set_cmd[10] = pv
            
            try:
                sock.send(set_cmd) 
            except socket.error as msg:
                print msg
                sock.close()
                sys.exit()  
          
            print hexlify(set_cmd), len(set_cmd)
            
        elif (x == 'q'):
            sock.close()
            break

    sys.exit()

