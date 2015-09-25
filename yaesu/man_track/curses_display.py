#!/usr/bin/env python
import os
import string
import sys
import time
import curses
import threading

class Display_Thread(threading.Thread):
    def __init__ (self, options, tt):
        threading.Thread.__init__(self)
        self._stop = threading.Event()
        self.screen = curses.initscr()
    	curses.noecho()
    	curses.curs_set(0)
    	self.screen.keypad(1)
    	self.screen.timeout(1000)
        self.tt = tt
        self.cmd_az         = 0.0       #Commanded Azimuth -180 to 180
        self.cmd_el         = 0.0       #Commanded Elevation 0 to 90
        self.current_az     = 0.0       #Current Azimuth
        self.current_az_adj = 0.0       #Current Azimuth
        self.current_el     = 0.0       #Current Elevation
        self.az_tol         = 0.0       #Azimuth Tolerance
        self.el_tol         = 0.0       #Elevation Tolerance
        self.status         = ""        #Antenna Pedestal Status
        self.target_az      = 180.0     #Target Azimuth, starts at -180
        self.target_el      = 0.0       #Target elevation, starts at 0
        self.update_flag    = False

    def run(self):
        KEY_DOWN = 258
        KEY_UP = 259
        KEY_LEFT = 260
        KEY_RIGHT = 261
        KEY_SPACE = 32
        KEY_ESC = 27
        KEY_ENTER = 10
        idx = 0
        self.Init_Display()
        while (not self._stop.isSet()):
            #Update_Sat_Menu(idx, screen, sat_list)
            event = self.screen.getch()
            if event == ord("q"): 
                break
            elif event == KEY_ESC: 
                break
            elif event == ord("a"): 
                self.set_target_az()
            elif event == ord("e"): 
                self.set_target_el()
            elif event == ord("u"): 
                self.send_update_msg()
            elif event == ord("s"): 
                self.stow_antennas()
            self.get_feedback()
            self.Update_Display()
        curses.endwin()    

    def set_target_az(self):
        #REFERENCE:  http://gnosis.cx/publish/programming/charming_python_6.html
        s = curses.newwin(3,50,20,5)
        s.box()
        s.addstr(1,2, "Enter Target Azimuth [0 to 360 deg]: ")
        s.refresh()
        curses.echo()
        tar_az_str = s.getstr()
        s.erase()
        self.target_az = float(tar_az_str)
        self.update_flag = False
        self.Init_Display()
        curses.noecho()

    def set_target_el(self):
        #REFERENCE:  http://gnosis.cx/publish/programming/charming_python_6.html
        s = curses.newwin(3,50,20,5)
        s.box()
        s.addstr(1,2, "Enter Target Elevation [0 to 90 deg]: ")
        s.refresh()
        curses.echo()
        tar_el_str = s.getstr()
        s.erase()
        self.target_el = float(tar_el_str)
        self.update_flag = False
        self.Init_Display()
        curses.noecho()

    def send_update_msg(self):
        self.tt.Write_Message(self.target_az, self.target_el)
        curses.flash()
        s = curses.newwin(3,25,20,5)
        s.box()
        for i in range(6):       
            s.addstr(1,2, "   Update Sent!!!    ", curses.A_REVERSE)
            s.refresh()
            time.sleep(0.1)
            s.addstr(1,2, "   Update Sent!!!    ", curses.A_NORMAL)
            s.refresh()
            time.sleep(0.1)
        s.erase()
        curses.flash()
        self.update_flag = True
        self.Init_Display()
        curses.noecho()

    def stow_antennas(self):
        #REFERENCE:  http://gnosis.cx/publish/programming/charming_python_6.html
        s = curses.newwin(5,65,10,3)
        s.box()
        s.addstr(1,2, "This will take a few minutes.")
        s.addstr(2,2, "Control of the tracker will be lost during Stow operations.")
        s.addstr(3,2, "Are you sure you want to continue (y/n)? ")
        s.refresh()
        curses.echo()
        stow_str = s.getstr()
        s.erase()
        self.Init_Display()
        curses.noecho()
        if stow_str == "y":
            self.tt.Write_Raw_Message("S")

    def get_feedback(self):
        self.cmd_az, self.cmd_el, self.current_az, self.current_el, self.az_tol, self.el_tol, self.status = self.tt.get_feedback()
        if self.current_az < 0:
            self.current_az_adj = 360 - (self.current_az * -1)
        else:
            self.current_az_adj = self.current_az
        
    def Update_Display(self):
        self.screen.addstr(5, 58,"    ")
        self.screen.addstr(5, 58, str(int(self.cmd_az)))
        self.screen.addstr(6, 58,"    ")
        self.screen.addstr(6, 58, str(int(self.cmd_el)))
        self.screen.addstr(7, 58,"    ")
        self.screen.addstr(7, 58, str(int(self.current_az)))
        self.screen.addstr(8, 58,"    ")
        self.screen.addstr(8, 58, str(int(self.current_el)))
        self.screen.addstr(9, 58,"    ")
        self.screen.addstr(9, 58, str(int(self.az_tol)))
        self.screen.addstr(10, 58,"    ")
        self.screen.addstr(10, 58, str(int(self.el_tol)))
        self.screen.addstr(11, 58,"    ")
        self.screen.addstr(11, 58, self.status)
        self.screen.addstr(14, 21,"    ")
        self.screen.addstr(14, 21, str(int(self.current_az_adj)))
        self.screen.addstr(16, 21,"    ")
        self.screen.addstr(16, 21, str(int(self.current_el)))
        self.screen.addstr(13, 21,"    ")
        self.screen.addstr(13, 21, str(int(self.target_az)))
        self.screen.addstr(15, 21,"    ")
        self.screen.addstr(15, 21, str(int(self.target_el)))
        self.screen.addstr(17, 21,"        ")
        self.screen.addstr(17, 21, str(self.update_flag))

    def Init_Display(self):
        self.screen.clear()
        self.screen.addstr(0, 0,"=================================================================", curses.A_REVERSE)        
        self.screen.addstr(1, 0,"                    Manual Tracking - VTGS                       ", curses.A_REVERSE)
        self.screen.addstr(2, 0,"=================================================================", curses.A_REVERSE)
#       self.screen.addstr(3, 0,"                                   ", curses.A_UNDERLINE)
        self.screen.addstr(4, 35,"        Raw Feedback         ", curses.A_REVERSE)
        self.screen.addstr(5, 35,"|   Commanded Azimuth:      |")
        self.screen.addstr(6, 35,"| Commanded Elevation:      |")
        self.screen.addstr(7, 35,"|     Current Azimuth:      |")
        self.screen.addstr(8, 35,"|   Current Elevation:      |")
        self.screen.addstr(9, 35,"|   Azimuth Tolerance:      |")
        self.screen.addstr(10,35,"| Elevation Tolerance:      |")
        self.screen.addstr(11,35,"|      Antenna Status:      |")
        self.screen.addstr(12,35,"|___________________________|")
        self.screen.addstr(4, 0, "      Keyboard Commands        ", curses.A_REVERSE)
        self.screen.addstr(5, 0, "|[a]: Update Target Azimuth   |")
        self.screen.addstr(6, 0, "|[e]: Update Target Elevation |")
        self.screen.addstr(7, 0, "|[u]: Send Update Command     |")
        self.screen.addstr(8, 0, "|[s]: Stow Antennas           |")
        self.screen.addstr(9, 0, "|[q]: QUIT                    |")
        self.screen.addstr(10,0, "|_____________________________|")
        self.screen.addstr(12, 0,"           Position            ", curses.A_REVERSE)
        self.screen.addstr(13, 0,"|    Target Azimuth:          |")
        self.screen.addstr(14, 0,"|   Current Azimuth:          |")
        self.screen.addstr(15, 0,"|  Target Elevation:          |")
        self.screen.addstr(16, 0,"| Current Elevation:          |")
        self.screen.addstr(17, 0,"|     Update Sent? :          |")
        self.screen.addstr(18, 0,"|_____________________________|")

    def stop(self):
        self._stop.set()

