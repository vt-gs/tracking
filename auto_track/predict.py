#!/usr/bin/env python
import socket
import os
import string
import sys
import time
import threading


class Predict_Thread(threading.Thread):
    def __init__ (self, options):
        threading.Thread.__init__(self)
        self._stop = threading.Event()
        self.ip = options.pred_ip
        self.port = options.pred_port
        self.sat_id = options.sat_id
        self.interval = options.interval
        self.suspend = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP Socket
        self.satellite = satellite()

    def run(self):
        while (not self._stop.isSet()):
            if self.suspend == False: self.Get_Sat_Data()
            time.sleep(self.interval)
        sys.exit()

    def get_feedback(self):
        return self.satellite
        
    def Get_Sat_Data(self):
        self.sock.sendto("GET_SAT "+ self.sat_id, (self.ip,self.port))
        rx_data = self.sock.recv(4096)
        sat_data = rx_data.split("\n")
        self.satellite.name = sat_data[0].strip()
        self.satellite.ssp_lat = float(sat_data[1])
        self.satellite.ssp_lon = float(sat_data[2])
        self.satellite.az = float(sat_data[3])
        self.satellite.el = float(sat_data[4])        
        self.satellite.aos_los = float(sat_data[5])
        self.satellite.footprint = float(sat_data[6])
        self.satellite.range = float(sat_data[7])
        self.satellite.altitude = float(sat_data[8])
        self.satellite.velocity = float(sat_data[9])
        self.satellite.orbit_number = float(sat_data[10])
        self.satellite.visibility = sat_data[11]
        self.satellite.orbit_phase = float(sat_data[12])
        self.satellite.eclipse_depth = float(sat_data[13])
        self.satellite.prop_delay = Get_Prop_Delay(self.satellite.range)
        self.sock.sendto("GET_DOPPLER "+ self.sat_id, (self.ip,self.port))
        rx_data2 = self.sock.recv(4096)
        sat_data2 = rx_data2.split("\n")
        self.satellite.doppler = float(sat_data2[0])

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

def Get_Prop_Delay(dist):
    c = 299.792458 #km/ms
    delay = dist / c
    return delay
    
def Calc_Doppler(norm_dopp, center_freq_dn, center_freq_up):
    #input:   radio center freq (Hz)
    #input:   doppler shift, normalized to 100 MHz (Hz)
    #output:  actual frequency
    true_dopp_dn = norm_dopp * (center_freq_dn / 100000000)
    true_dopp_up = -1 * norm_dopp * (center_freq_up / 100000000)
    return true_dopp_dn, true_dopp_up

class satellite(object):
    def __init__(self, sat_name=""):
        self.name = sat_name
        self.az = 0
        self.el = 0
        self.ssp_lat = 0
        self.ssp_lon = 0
        self.aos_los = 0
        self.footprint = 0
        self.range = 0
        self.altitude = 0
        self.velocity = 0
        self.orbit_number = 0
        self.visibility = ""
        self.orbit_phase = 0
        self.eclipse_depth = 0
        self.doppler = 0
        self.prop_delay = 0
        self.dopp_dn = 0
        self.dopp_up =0
        self.up_freq = 0
        self.dn_freq = 0


