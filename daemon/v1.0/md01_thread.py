#!/usr/bin/env python
##################################################
# GPS Interface
# Author: Zach Leffke
# Description: Initial GPS testing
##################################################

from optparse import OptionParser
import threading
from datetime import datetime as date
import os
import math
import sys
import string
import time

def getTimeStampGMT(self):
    return str(date.utcnow()) + " GMT | "

class MD01_Thread(threading.Thread):
    def __init__ (self, ip = '192.168.42.21', port = 2000):
        threading.Thread.__init__(self)
        self._stop  = threading.Event()
        self.md01   = md01(ip, port)
        self.connected = False

    def run(self):
        
        while (not self._stop.isSet()):
            pass
            time.sleep(1)
        sys.exit()

    def stop(self):
        self.gps_ser.close()
        self._stop.set()
        sys.quit()

    def stopped(self):
        return self._stop.isSet()


