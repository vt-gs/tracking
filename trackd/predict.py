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
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP Socket
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

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

def Get_Sat_Data(predict_ip, predict_port, sat_name, sock):
	temp_sat = satellite(sat_name)
	sock.sendto("GET_SAT "+ sat_name, (predict_ip,predict_port))
	rx_data = sock.recv(4096)
	sat_data = rx_data.split("\n")
	temp_sat.ssp_lat = float(sat_data[1])
	temp_sat.ssp_lon = float(sat_data[2])
	temp_sat.az = float(sat_data[3])
	temp_sat.el = float(sat_data[4])		
	temp_sat.aos_los = float(sat_data[5])
	temp_sat.footprint = float(sat_data[6])
	temp_sat.range = float(sat_data[7])
	temp_sat.altitude = float(sat_data[8])
	temp_sat.velocity = float(sat_data[9])
	temp_sat.orbit_number = float(sat_data[10])
	temp_sat.visibility = sat_data[11]
	temp_sat.orb_phase = float(sat_data[12])
	temp_sat.eclipse_depth = float(sat_data[13])
	temp_sat.prop_delay = Get_Prop_Delay(temp_sat.range)
	sock.sendto("GET_DOPPLER "+ sat_name, (predict_ip,predict_port))
	rx_data2 = sock.recv(4096)
	sat_data2 = rx_data2.split("\n")
	temp_sat.doppler = float(sat_data2[0])
	return temp_sat

def Get_Prop_Delay(dist):
	c = 299.792458 #km/ms
	delay = dist / c
	return delay
	
def Log_Data(log_file, sat, ts):
	entry = str(ts) + "," + str(sat.az) + "," + str(sat.el) + "," 
	entry = entry + str(int(sat.dopp_dn)) + "," + str(int(sat.dn_freq)) + ","
	entry = entry + str(int(sat.dopp_up)) + "," + str(int(sat.up_freq)) + ","
	entry = entry + str(sat.prop_delay) + ",\n"
	log_file.write(entry)

def Calc_Doppler(norm_dopp, center_freq_dn, center_freq_up):
	#input:   radio center freq (Hz)
	#input:   doppler shift, normalized to 100 MHz (Hz)
	#output:  actual frequency
	true_dopp_dn = norm_dopp * (center_freq_dn / 100000000)
	true_dopp_up = -1 * norm_dopp * (center_freq_up / 100000000)
	return true_dopp_dn, true_dopp_up

class satellite(object):
	def __init__(self, sat_name):
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
		self.orb_phase = 0
		self.eclipse_depth = 0
		self.doppler = 0
		self.prop_delay = 0
		self.dopp_dn = 0
		self.dopp_up =0
		self.up_freq = 0
		self.dn_freq = 0

def Initialize_Sat_Data(predict_ip, predict_port, sats, sat_list, sock):
    #This function builds up the sats oject list according to whats is currently active on Predict Server
    for i in range(len(sat_list)):
        sats.append(satellite(sat_list[i]))
        sats[i] = Get_Sat_Data(predict_ip, predict_port, sats[i].name, sock)

def Update_Sat_Data(predict_ip, predict_port, sats, sock):
    for i in range(len(sats)):
        sats[i] = Get_Sat_Data(predict_ip, predict_port, sats[i].name, sock)

def Get_Sat_List(predict_ip, predict_port, sock):
	sock.sendto("GET_LIST", (predict_ip, predict_port))	
	rx_data = sock.recv(4096)
	sat_list = rx_data.strip().split("\n")
	#print "Satellite List Up To Date"
	return sat_list


