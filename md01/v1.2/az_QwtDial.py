#!/usr/bin/env python

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import Qt
import PyQt4.Qwt5 as Qwt
import numpy as np
import sys

class overlayLabel(QtGui.QLabel):    
    def __init__(self, parent=None, text = "", pixelSize=20, r=255,g=255,b=255, underline=True, bold=True):        
        super(overlayLabel, self).__init__(parent)
        self.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        palette = QtGui.QPalette(self.palette())
        palette.setColor(palette.Background,QtCore.Qt.transparent)
        palette.setColor(palette.Foreground,QtGui.QColor(r,g,b))
        self.setPalette(palette)
        font = QtGui.QFont()
        font.setBold(bold)
        font.setPixelSize(pixelSize)
        font.setUnderline(underline)
        self.setFont(font)
        #self.setGeometry(2,2,100,25)
        self.setText(text)

class overlayLCD(QtGui.QLCDNumber):    
    def __init__(self, parent=None, feedback_bool=True):        
        super(overlayLCD, self).__init__(parent)
        self.setSegmentStyle(QtGui.QLCDNumber.Flat)
        palette = QtGui.QPalette(self.palette())
        palette.setColor(palette.Background,QtCore.Qt.transparent)
        if feedback_bool == True: 
            palette.setColor(palette.Foreground,QtGui.QColor(255,0,0))
            self.setGeometry(10,315,85,30)
        else: 
            palette.setColor(palette.Foreground,QtGui.QColor(0,0,255))
            self.setGeometry(245,315,85,30)
        self.setPalette(palette)
        self.display(0)

class az_QwtDial(Qwt.QwtDial):
    def __init__(self, parent=None):
        super(az_QwtDial, self).__init__(parent)
        self.parent = parent
        self.needle = Qwt.QwtDialSimpleNeedle(Qwt.QwtDialSimpleNeedle.Ray, 1, QtGui.QColor(255,0,0))
        self.setOrigin(270)
        self.initUI()
        #self.setGeometry(5,5,330,330)
        self.move(5,5)
        self.resize(330,330)

    def initUI(self):
        self.setFrameShadow(Qwt.QwtDial.Plain)
        self.needle.setWidth(4)
        self.setNeedle(self.needle)
        self.setValue(0)
        self.setScaleTicks(5,10,15,1)
        self.setStyleSheet("Qlabel {font-size:14px;}")

        palette = QtGui.QPalette()
        palette.setColor(palette.Base,QtCore.Qt.transparent)
        palette.setColor(palette.WindowText,QtCore.Qt.transparent)
        palette.setColor(palette.Text,QtCore.Qt.green)
        self.setPalette(palette)
        
        self.title_label = overlayLabel(self.parent, "Azimuth")
        self.title_label.setGeometry(2,2,100,25)
        self.cur_label = overlayLabel(self.parent, "Current", 15, 255,0,0,False, True)
        self.cur_label.setGeometry(10,293,60,25)
        self.cur_label.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)

        self.tar_label = overlayLabel(self.parent, "Target", 15, 0,0,255,False,True)
        self.tar_label.setGeometry(280,293,50,25)
        self.tar_label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)

        self.cur_lcd = overlayLCD(self.parent, True)
        self.tar_lcd = overlayLCD(self.parent, False)
        self.overlayDial = overlayAzQwtDial(self.parent)

    def set_cur_az(self, az):
        self.cur_lcd.display(az)
        if    (az < -180)                  : az = -180
        elif ((az >= -180) and (az < 0))   : az = 360 + az
        elif ((az >= 0)    and (az <= 360)): az = az
        elif ((az > 360)   and (az <= 540)): az = az - 360
        elif  (az > 540)                   : az = 180
        self.setValue(az)

    def set_tar_az(self, az):
        self.tar_lcd.display(az)
        if    (az < -180)                  : az = -180
        elif ((az >= -180) and (az < 0))   : az = 360 + az
        elif ((az >= 0)    and (az <= 360)): az = az
        elif ((az > 360)   and (az <= 540)): az = az - 360
        elif  (az > 540)                   : az = 180
        self.overlayDial.setValue(az)

class overlayAzQwtDial(Qwt.QwtDial):
    def __init__(self, parent=None):
        super(overlayAzQwtDial, self).__init__(parent)
        self.parent = parent
        self.needle = Qwt.QwtDialSimpleNeedle(Qwt.QwtDialSimpleNeedle.Ray, 1, QtGui.QColor(0,0,255))
        self.setOrigin(270)
        #ipdb.set_trace()
        self.initUI()
        self.move(5,5)
        self.resize(330,330)
        #self.setGeometry(5,5,330,330)

    def initUI(self):
        self.setFrameShadow(Qwt.QwtDial.Plain)
        self.needle.setWidth(2)
        self.setNeedle(self.needle)
        self.setValue(0)
        self.setScaleTicks(5,10,15,1)
        self.setStyleSheet("Qlabel {font-size:14px;}")

        palette = QtGui.QPalette()
        palette.setColor(palette.Base,QtCore.Qt.transparent)
        palette.setColor(palette.WindowText,QtCore.Qt.transparent)
        palette.setColor(palette.Text,QtCore.Qt.transparent)
        self.setPalette(palette)

    def set_az(self, az):
        self.setValue(az)
