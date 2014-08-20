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
        print msg
        #

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

class Display_Thread(threading.Thread):
    def __init__ (self, options, pt):
        threading.Thread.__init__(self)
        self._stop = threading.Event()
        self.screen = curses.initscr()
    	curses.noecho()
    	curses.curs_set(0)
    	self.screen.keypad(1)
    	self.screen.timeout(1000)
        self.pt = pt
        self.sat_list = pt.get_sat_list()

    def run(self):
        KEY_DOWN = 258
        KEY_UP = 259
        KEY_LEFT = 260
        KEY_RIGHT = 261
        KEY_SPACE = 32
        KEY_ESC = 27
        KEY_ENTER = 10
        idx = 0
        self.Sat_List_Menu()
        while (not self._stop.isSet()):
            #Update_Sat_Menu(idx, screen, sat_list)
            event = self.screen.getch()
            if event == KEY_DOWN:
                if idx < (len(self.sat_list)): idx += 1
            elif event == KEY_UP:
                if idx > 0: idx += -1
            #elif event == KEY_ENTER:
                #Display_Sat_Data(predict_ip, predict_port, screen, sats[idx])
                #Sat_List_Menu(screen, sat_list)
            elif event == ord("q"): break
            elif event == KEY_ESC: break	
        curses.endwin()    

    def Sat_List_Menu(self):
        mypad = curses.newpad(40,60)
        mypad_pos = 0
        mypad.refresh(mypad_pos, 0, 5, 5, 10, 60)
        while 1:
            cmd = mypad.getch()
            if  cmd == curses.KEY_DOWN:
                mypad_pos += 1
                mypad.refresh(mypad_pos, 0, 5, 5, 10, 60)
            elif cmd == curses.KEY_UP:
                mypad_pos -= 1
                mypad.refresh(mypad_pos, 0, 5, 5, 10, 60)
            elif cmd == ord("q"): break

    def Sat_List_Menu_OLD(self):
        self.screen.clear()
        self.screen.addstr(0,0, "Satellite Menu", curses.A_UNDERLINE)
        self.screen.addstr(22,1, "press <ENTER> to Select Satellite")
        self.screen.addstr(23,1, "press 'q' to Quit")
        for i in range(len(self.pt.sat_list)):
            if i >= 17:
                y_idx = i + 2 - 17
                x_idx = 40
            else:
                y_idx = i + 2
                x_idx = 5
            self.screen.addstr(y_idx, x_idx, self.sat_list[i])

    def stop(self):
        self._stop.set()

if __name__ == '__main__':
	
    #--------START Command Line option parser------------------------------------------------
    usage = "usage: %prog -a <Server Address> -p <Server Port> "
    parser = OptionParser(usage = usage)
    s_help = "IP address of tracker, Default: 127.0.0.1"
    p_help = "TCP port number of tracker, Default: 196"
    parser.add_option("-a", dest = "ip"  , action = "store", type = "string", default = "127.0.0.1", help = s_help)
    parser.add_option("-p", dest = "port", action = "store", type = "int"   , default = "196"      , help = p_help)
    (options, args) = parser.parse_args()
    #--------END Command Line option parser-------------------------------------------------

    tt = Tracker_Thread(options)
    #dt = Display_Thread(options, pt)
    tt.daemon = True
    #dt.daemon = True
    tt.run()
    #dt.run()
    print "terminating, please wait..."
    #tt.stop()
    #dt.stop()
    #pt.join()
    sys.exit()
