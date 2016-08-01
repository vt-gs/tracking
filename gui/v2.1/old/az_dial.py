#!/usr/bin/env python

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import Qt
import PyQt4.Qwt5 as Qwt
import numpy as np
import sys

class AzimuthFrame(QtGui.QFrame):
    def __init__(self, parent=None):
        super(AzimuthFrame, self).__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.grid = QtGui.QGridLayout()
        self.dial = AzimuthDial(self)
        #self.grid.addWidget(self.dial,0,0,20,20)
        self.setLayout(self.grid)

class AzimuthDial(Qwt.QwtDial):
    def __init__(self, parent=None):
        super(AzimuthDial, self).__init__(parent)
        self.parent = parent
        #self.needle = Qwt.QwtDialSimpleNeedle(Qwt.QwtDialSimpleNeedle.Ray, 1, QtGui.QColor(255,0,0))
        self.needle = Qwt.QwtDialSimpleNeedle(Qwt.QwtDialSimpleNeedle.Arrow, 1, QtGui.QColor(255,0,0))
        self.setOrigin(270)
        self.init_ui()

    def init_ui(self):
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
        self.overlayDial = overlayAzQwtDial()
        #self.parent.grid.addWidget(self,0,0,15,15)
        self.parent.grid.addWidget(self,0,0)
        #self.parent.grid.addWidget(self.overlayDial,0,0,15,15)
        self.parent.grid.addWidget(self.overlayDial,0,0)

        #self.cur_label = overlayLabel(self, "Current", 15, 255,0,0,False, True)
        #self.cur_label.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignBottom)
        #self.parent_grid.addWidget(self.cur_label,12,0,1,1)

        #self.tar_label = overlayLabel(self, "Target", 15, 0,0,255,False,True)
        #self.tar_label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignBottom)
        #self.parent_grid.addWidget(self.tar_label,12,14,1,1)

        #self.cur_lcd = overlayLCD(self, True)
        #self.parent_grid.addWidget(self.cur_lcd,13,0,2,1)
        
        #self.tar_lcd = overlayLCD(self, False)
        #self.parent_grid.addWidget(self.tar_lcd,13,14,2,1)

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
    def __init__(self, parent=None, feedback_bool=True):        
        super(overlayLCD, self).__init__(parent)
        self.setSegmentStyle(QtGui.QLCDNumber.Flat)
        palette = QtGui.QPalette(self.palette())
        palette.setColor(palette.Background,QtCore.Qt.transparent)
        if feedback_bool == True: palette.setColor(palette.Foreground,QtGui.QColor(255,0,0))
        else: palette.setColor(palette.Foreground,QtGui.QColor(0,0,255))
        self.setPalette(palette)
        self.setFixedHeight(30)
        self.setFixedWidth(85)
        self.display(0)


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
