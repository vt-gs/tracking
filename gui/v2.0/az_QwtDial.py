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
        self.setText(text)

class overlayLCD(QtGui.QLCDNumber):    
    def __init__(self, parent=None, feedback_bool=0):        
        super(overlayLCD, self).__init__(parent)
        self.setSegmentStyle(QtGui.QLCDNumber.Flat)
        palette = QtGui.QPalette(self.palette())
        palette.setColor(palette.Background,QtCore.Qt.transparent)
        if feedback_bool == 0: palette.setColor(palette.Foreground,QtGui.QColor(255,0,0))
        elif feedback_bool == 1: palette.setColor(palette.Foreground,QtGui.QColor(0,0,255))
        elif feedback_bool == 2: palette.setColor(palette.Foreground,QtGui.QColor(255,0,255))
        self.setPalette(palette)
        self.setFixedHeight(30)
        self.setFixedWidth(85)
        self.display(000.0)

class az_QwtDial(Qwt.QwtDial):
    def __init__(self, parent_grid):
        super(az_QwtDial, self).__init__()
        self.parent_grid = parent_grid
        #self.needle = Qwt.QwtDialSimpleNeedle(Qwt.QwtDialSimpleNeedle.Ray, 1, QtGui.QColor(255,0,0))
        self.needle = Qwt.QwtDialSimpleNeedle(Qwt.QwtDialSimpleNeedle.Arrow, 1, QtGui.QColor(255,0,0))
        self.setOrigin(270)
        self.initUI()

    def initUI(self):
        self.setFrameShadow(Qwt.QwtDial.Plain)
        self.needle.setWidth(15)
        self.setNeedle(self.needle)
        self.setValue(0)
        self.setScaleTicks(5,10,15,1)
        self.setStyleSheet("Qlabel {font-size:14px;}")

        palette = QtGui.QPalette()
        palette.setColor(palette.Base,QtCore.Qt.transparent)
        palette.setColor(palette.WindowText,QtCore.Qt.transparent)
        palette.setColor(palette.Text,QtCore.Qt.green)
        self.setPalette(palette)
        
        self.title_label = overlayLabel(self, "Azimuth")
        #self.parent_grid.addWidget(self.title_label,0,6)
        self.overlayDial = overlayAzQwtDial()
        self.parent_grid.addWidget(self,0,0,30,30)
        self.parent_grid.addWidget(self.overlayDial,0,0,30,30)
        #self.parent_grid.setRowStretch(15,1)

        self.cur_label = overlayLabel(self, "Current", 15, 255,0,0,False, True)
        self.cur_label.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignBottom)
        self.parent_grid.addWidget(self.cur_label,27,0,1,1)

        self.tar_label = overlayLabel(self, "Target", 15, 0,0,255,False,True)
        self.tar_label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignBottom)
        self.parent_grid.addWidget(self.tar_label,27,29,1,1)

        #self.rate_label = overlayLabel(self, "0.000", 15, 255,0,255,False,True)
        #self.rate_label.setAlignment(QtCore.Qt.AlignCenter|QtCore.Qt.AlignBottom)
        #self.parent_grid.addWidget(self.rate_label,28,1,2,28)

        self.cur_lcd = overlayLCD(self, 0)
        self.parent_grid.addWidget(self.cur_lcd,28,0,2,1)

        self.rate_lcd = overlayLCD(self, 2)
        self.parent_grid.addWidget(self.rate_lcd,28,15,2,1)
        
        self.tar_lcd = overlayLCD(self, 1)
        self.parent_grid.addWidget(self.tar_lcd,28,29,2,1)

    def set_cur_az(self, az):
        self.cur_lcd.display(az)
        if    (az < -180)                  : az = -180
        elif ((az >= -180) and (az < 0))   : az = 360 + az
        elif ((az >= 0)    and (az <= 360)): az = az
        elif ((az > 360)   and (az <= 540)): az = az - 360
        elif  (az > 540)                   : az = 180
        self.setValue(az)
    
    def set_cur_rate(self, rate):
        self.rate_label.setText('{:1.3f}'.format(rate))

    def set_tar_az(self, az):
        self.tar_lcd.display(az)
        if    (az < -180)                  : az = -180
        elif ((az >= -180) and (az < 0))   : az = 360 + az
        elif ((az >= 0)    and (az <= 360)): az = az
        elif ((az > 360)   and (az <= 540)): az = az - 360
        elif  (az > 540)                   : az = 180
        self.overlayDial.setValue(az)

class overlayAzQwtDial(Qwt.QwtDial):
    def __init__(self):
        super(overlayAzQwtDial, self).__init__()
        self.needle = Qwt.QwtDialSimpleNeedle(Qwt.QwtDialSimpleNeedle.Ray, 1, QtGui.QColor(0,0,255))
        #self.needle = Qwt.QwtDialSimpleNeedle(Qwt.QwtDialSimpleNeedle.Arrow, 1, QtGui.QColor(0,0,255))
        self.setOrigin(270)
        self.initUI()

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
