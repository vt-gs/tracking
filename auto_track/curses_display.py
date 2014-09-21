#!/usr/bin/env python
import os
import string
import sys
import time
import curses
import threading
from predict import *

class Display_Thread(threading.Thread):
    def __init__ (self, options, tt, pt):
        threading.Thread.__init__(self)
        self._stop = threading.Event()
        self.screen = curses.initscr()
    	curses.noecho()
    	curses.curs_set(0)
    	self.screen.keypad(1)
    	self.screen.timeout(int(1000*options.interval))
        self.tt = tt
        self.pt = pt
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
        self.satellite = satellite()

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
            elif event == ord("p"): 
                self.suspend_predict()
            elif event == ord("t"): 
                self.suspend_tracker()
            elif event == ord("s"): 
                self.stow_antennas()
            self.get_feedback()
            self.Update_Tracker_Display()
            self.Update_Predict_Display()
        curses.endwin()    

    
    def send_update_msg(self):
        self.tt.Write_Message(self.target_az, self.target_el)
        
    def suspend_predict(self):
        if self.pt.suspend == False:
            self.pt.suspend = True
            self.screen.addstr(21, 16, "         ")
            self.screen.addstr(21, 16, "Enabled ")
        elif self.pt.suspend == True:
            self.pt.suspend = False
            self.screen.addstr(21, 16, "         ")
            self.screen.addstr(21, 16, "Disabled ")
    
    def suspend_tracker(self):
        if self.tt.suspend == False:
            self.tt.suspend = True
            self.screen.addstr(20, 16, "         ")
            self.screen.addstr(20, 16, "Enabled ")
        elif self.tt.suspend == True:
            self.tt.suspend = False
            self.screen.addstr(20, 16, "         ")
            self.screen.addstr(20, 16, "Disabled ")

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
        self.satellite = self.pt.get_feedback()
        
    def Update_Tracker_Display(self):
        self.screen.addstr(5, 23,"    ")
        self.screen.addstr(5, 23, str(int(self.cmd_az)))
        self.screen.addstr(6, 23,"    ")
        self.screen.addstr(6, 23, str(int(self.cmd_el)))
        self.screen.addstr(7, 23,"    ")
        self.screen.addstr(7, 23, str(int(self.current_az)))
        self.screen.addstr(8, 23,"    ")
        self.screen.addstr(8, 23, str(int(self.current_el)))
        self.screen.addstr(9, 23,"    ")
        self.screen.addstr(9, 23, str(int(self.az_tol)))
        self.screen.addstr(10, 23,"    ")
        self.screen.addstr(10, 23, str(int(self.el_tol)))
        self.screen.addstr(11, 23,"    ")
        self.screen.addstr(11, 23, self.status)
        self.screen.addstr(15, 23,"    ")
        self.screen.addstr(15, 23, str(int(self.current_az_adj)))
        self.screen.addstr(17, 23,"    ")
        self.screen.addstr(17, 23, str(int(self.current_el)))
        self.screen.addstr(14, 23,"    ")
        self.screen.addstr(14, 23, str(int(self.target_az)))
        self.screen.addstr(16, 23,"    ")
        self.screen.addstr(16, 23, str(int(self.target_el)))

    def Update_Predict_Display(self):
        self.screen.addstr(5, 53,"                    ")
        self.screen.addstr(5, 53, str(self.satellite.name))
        self.screen.addstr(6, 53,"                    ")
        self.screen.addstr(6, 53, str(self.satellite.ssp_lat))
        self.screen.addstr(7, 53,"                    ")
        self.screen.addstr(7, 53, str(self.satellite.ssp_lon))
        self.screen.addstr(8, 53,"                    ")
        self.screen.addstr(8, 53, str(self.satellite.az))
        self.screen.addstr(9, 53,"                    ")
        self.screen.addstr(9, 53, str(self.satellite.el))
        self.screen.addstr(10,53,"                    ")
        self.screen.addstr(10,53, str(self.satellite.aos_los - time.time()))
        self.screen.addstr(11,53,"                    ")
        self.screen.addstr(11,53, str(self.satellite.footprint))
        self.screen.addstr(12,53,"                    ")
        self.screen.addstr(12,53, str(self.satellite.range))
        self.screen.addstr(13,53,"                    ")
        self.screen.addstr(13,53, str(self.satellite.altitude))
        self.screen.addstr(14,53,"                    ")
        self.screen.addstr(14,53, str(self.satellite.velocity))
        self.screen.addstr(15,53,"                    ")
        self.screen.addstr(15,53, str(self.satellite.orbit_number))
        self.screen.addstr(16,53,"                    ")
        self.screen.addstr(16,53, str(self.satellite.visibility))
        self.screen.addstr(17,53,"                    ")
        self.screen.addstr(17,53, str(self.satellite.orbit_phase))
        self.screen.addstr(18,53,"                    ")
        self.screen.addstr(18,53, str(self.satellite.eclipse_depth))
        self.screen.addstr(19,53,"                    ")
        self.screen.addstr(19,53, str(self.satellite.prop_delay))
        self.screen.addstr(20,53,"                    ")
        self.screen.addstr(20,53, str(self.satellite.doppler))

    def Init_Display(self):
        self.screen.clear()
        self.screen.addstr(0, 0,"==============================================================================", curses.A_REVERSE)        
        self.screen.addstr(1, 0,"                    Auto Tracking - VTGS                                      ", curses.A_REVERSE)
        self.screen.addstr(2, 0,"==============================================================================", curses.A_REVERSE)
#       self.screen.addstr(3, 0,"                                   ", curses.A_UNDERLINE)
        self.screen.addstr(4, 31,"                Predict Feedback              ", curses.A_REVERSE)
        self.screen.addstr(5, 31,"|     Satellite Name:                         |")
        self.screen.addstr(6, 31,"|     Latitude [deg]:                         |")
        self.screen.addstr(7, 31,"|    Longitude [deg]:                         |")
        self.screen.addstr(8, 31,"|      Azimuth [deg]:                         |")
        self.screen.addstr(9, 31,"|    Elevation [deg]:                         |")
        self.screen.addstr(10,31,"|   Next AOS/LOS [s]:                         |")
        self.screen.addstr(11,31,"|     Footprint [km]:                         |")
        self.screen.addstr(12,31,"|         Range [km]:                         |")
        self.screen.addstr(13,31,"|      Altitude [km]:                         |")
        self.screen.addstr(14,31,"|    Velocity [km/s]:                         |")
        self.screen.addstr(15,31,"|       Orbit Number:                         |")
        self.screen.addstr(16,31,"|         Visibility:                         |")
        self.screen.addstr(17,31,"|        Orbit Phase:                         |")
        self.screen.addstr(18,31,"|      Eclipse Depth:                         |")
        self.screen.addstr(19,31,"|    Prop Delay [ms]:                         |")
        self.screen.addstr(20,31,"|Doppler@100MHz [Hz]:                         |")
        self.screen.addstr(21,31,"|_____________________________________________|")

        self.screen.addstr(4, 0, "      Tracker Feedback       ", curses.A_REVERSE)
        self.screen.addstr(5, 0, "|   Commanded Azimuth:      |")
        self.screen.addstr(6, 0, "| Commanded Elevation:      |")
        self.screen.addstr(7, 0, "|     Current Azimuth:      |")
        self.screen.addstr(8, 0, "|   Current Elevation:      |")
        self.screen.addstr(9, 0, "|   Azimuth Tolerance:      |")
        self.screen.addstr(10,0, "| Elevation Tolerance:      |")
        self.screen.addstr(11,0, "|      Antenna Status:      |")
        self.screen.addstr(12,0, "|___________________________|")
        self.screen.addstr(13,0, "      Antenna Position       ", curses.A_REVERSE)
        self.screen.addstr(14,0, "|      Target Azimuth:      |")
        self.screen.addstr(15,0, "|     Current Azimuth:      |")
        self.screen.addstr(16,0, "|    Target Elevation:      |")
        self.screen.addstr(17,0, "|   Current Elevation:      |")
        self.screen.addstr(18,0, "|___________________________|")
        self.screen.addstr(20, 0, "Tracker Status: Enabled ")
        self.screen.addstr(21, 0, "Predict Status: Enabled ")
        self.screen.addstr(23, 0, "[q]:Quit [p]:Suspend Predict [t]:Suspend Tracker [s]:Stow Antennas")#, curses.A_REVERSE)

    def stop(self):
        self._stop.set()

