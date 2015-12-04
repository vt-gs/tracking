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
        self.setGeometry(5,5,100,25)
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

class el_QwtDial(Qwt.QwtDial):
    def __init__(self, parent=None):
        super(el_QwtDial, self).__init__(parent)
        self.parent = parent
        self.needle = Qwt.QwtDialSimpleNeedle(Qwt.QwtDialSimpleNeedle.Ray, 1, QtGui.QColor(255,0,0))
        self.setOrigin(180)
        self.initUI()
        self.setGeometry(5,5,330,330)
        
    def initUI(self):
        self.setFrameShadow(Qwt.QwtDial.Plain)
        self.needle.setWidth(4)
        self.setNeedle(self.needle)
        self.setScaleArc(0,180)
        self.setRange(0,180)
        self.setScale(10, 10, 10)
        self.setValue(0)
        self.setScaleTicks(5,10,15,1)
        self.setStyleSheet("QwtDial {font-size: 14px;}")

        palette = QtGui.QPalette()
        palette.setColor(palette.Base,QtCore.Qt.transparent)
        palette.setColor(palette.WindowText,QtCore.Qt.transparent)
        palette.setColor(palette.Text,QtCore.Qt.green)
        self.setPalette(palette)

        self.title_label = overlayLabel(self.parent, "Elevation")
        self.title_label.setGeometry(2,2,100,25)
        self.cur_label = overlayLabel(self.parent, "Current", 15, 255,0,0,False, True)
        self.cur_label.setGeometry(10,293,60,25)
        self.cur_label.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)

        self.tar_label = overlayLabel(self.parent, "Target", 15, 0,0,255,False,True)
        self.tar_label.setGeometry(280,293,50,25)
        self.tar_label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)







        self.cur_lcd = overlayLCD(self.parent, True)
        self.tar_lcd = overlayLCD(self.parent, False)
        self.overlayDial = overlayElQwtDial(self.parent)

    def set_cur_el(self, el):
        self.setValue(el)
        self.cur_lcd.display(el)

    def set_tar_el(self, el):
        self.overlayDial.setValue(el)
        self.tar_lcd.display(el)

class overlayElQwtDial(Qwt.QwtDial):
    def __init__(self, parent=None):
        super(overlayElQwtDial, self).__init__(parent)
        self.parent = parent
        self.needle = Qwt.QwtDialSimpleNeedle(Qwt.QwtDialSimpleNeedle.Ray, 1, QtGui.QColor(0,0,255))
        self.setOrigin(180)
        self.initUI()
        self.setGeometry(5,5,330,330)
        
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

    def set_el(self, el):
        self.setValue(el)


