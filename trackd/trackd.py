#!/usr/bin/env python
import socket
import os
import string
import sys
import time
import curses
from threading import Thread
from optparse import OptionParser
from predict import *



class Predict_Thread(Thread):
    def __init__ (self, options):
        Thread.__init__(self)
        #super(Predict_Thread, self).__init__()
        self._stop = threading.Event()
        self.pred_ip = options.pred_ip
        self.pred_port = options.pred_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Create UDP socket
        self.sat_list = Get_Sat_List(self.pred_ip, self.pred_port, self.sock)
        self.sats = []  #Create Satellite object list, comprised of object 'satellite'
        Initialize_Sat_Data(self.pred_ip, self.pred_port, self.sats, self.sat_list, self.sock)
        
    def run(self):
        while (not self._stop.isSet()):
            Update_Sat_Data(self.pred_ip, self.pred_port, self.sats, self.sock)
            time.sleep(1)
            #print "hello"

    def stop(self):
        self._stop.set()

    def get_sat(self, sat_name):
        #Returns satellite object from sat_list
        sat = satellite('null')
        for i in range(len(self.sats)):
            if sats[i].name == sat_name: 
                sat = sats[i]
                break
        return sat

    def get_sat_list(self):
        return self.sat_list


class Display_Thread(Thread):
    def __init__ (self, options, pt):
        Thread.__init__(self)
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
    s_help = "IP address or hostname of server, Default: 128.173.144.68"
    p_help = "port number of server for incoming connections, Default: 1210"
    parser.add_option("-a", dest = "pred_ip"  , action = "store", type = "string", default = "128.173.144.68", help = s_help)
    parser.add_option("-p", dest = "pred_port", action = "store", type = "int"   , default = "1210"          , help = p_help)
    (options, args) = parser.parse_args()
    #--------END Command Line option parser-------------------------------------------------

    pt = Predict_Thread(options)
    dt = Display_Thread(options, pt)
    pt.daemon = True
    dt.daemon = True
    pt.start()
    dt.run()
    print "terminating, please wait..."
    pt.stop()
    dt.stop()
    #pt.join()
    sys.exit()
