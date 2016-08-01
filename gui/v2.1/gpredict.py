#!/usr/bin/env python
#version 2.1

import socket
import os
import string
import sys
import time
from datetime import datetime as date
import threading

class Gpredict_Thread(threading.Thread):
    def __init__ (self, parent=None, ip="127.0.0.1", port=4533,timeout=1):
        threading.Thread.__init__(self)
        self._stop      = threading.Event()
        self.ip         = ip
        self.port       = port
        self.sock       = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #To allow socket reuse
        self.timeout    = timeout
        self.sock.settimeout(self.timeout)
        self.parent     = parent
        

        self.connected  = 0 #0 = disconnected, 1 = listening, 2 = connected

        self.tar_az     = 0.0
        self.tar_el     = 0.0
        self.cur_az     = 0.0
        self.cur_el     = 0.0

    def run(self):
        print self.utc_ts() + "Gpredict Thread Started..."
        self.sock.bind((self.ip, self.port))
        self.sock.listen(1)
        self.connected = 1 #listening
        self.parent.set_predict_conn_state(self.connected)
        while (not self._stop.isSet()):
            try:
                if self.connected == 1: #listening
                    conn, addr = self.sock.accept()
                    self.connected = 2 #connected
                    self.parent.set_predict_conn_state(self.connected)
                    print self.utc_ts() + 'Connection address:', addr
                if self.connected == 2: #client connected
                    data = conn.recv(1024)
                    if data.strip('\n') == 'p':
                        self.cur_az, self.cur_el = self.parent.predict_callback_get()
                        resp = str(self.cur_az) + "\n" + str(self.cur_el) + "\n"
                        conn.send(resp)  # echo
                    elif data.strip('\n')[0] == 'P':
                        self.updateTargetAngles(data)
                        conn.send('\n')  # echo
                    elif data.strip('\n') == 'q':
                        print self.utc_ts() + "Gpredict Hung Up..."
                        conn.close()
                        self.connected = 0
                        self.parent.set_predict_conn_state(self.connected)
            except socket.error as msg:
                #print self.utc_ts() + str(msg)
                time.sleep(1)
    
    def getConnectionStatus(self):
        return self.connected

    def updateTargetAngles(self, data):
        i = data.find(' ', 5, 10)
        az_str = data[2:i]
        el_str = data[i+1:]
        self.tar_az = float(az_str.strip())
        self.tar_el = float(el_str.strip())
        self.parent.predict_callback_set(self.tar_az, self.tar_el)

    def getTargetAngles(self):
        return self.tar_az, self.tar_el

    def updateCurrentAngles(self, az, el):
        self.cur_az = az
        self.cur_el = el

    def utc_ts(self):
        return str(date.utcnow()) + " UTC | PRD | "

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()
