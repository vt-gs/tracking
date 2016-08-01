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

class el_QwtDial(Qwt.QwtDial):
    def __init__(self, parent_grid):
        super(el_QwtDial, self).__init__()
        self.parent_grid = parent_grid
        #self.needle = Qwt.QwtDialSimpleNeedle(Qwt.QwtDialSimpleNeedle.Ray, 1, QtGui.QColor(255,0,0))
        self.needle = Qwt.QwtDialSimpleNeedle(Qwt.QwtDialSimpleNeedle.Arrow, 1, QtGui.QColor(255,0,0))
        self.setOrigin(180)
        self.initUI()
        
    def initUI(self):
        self.setFrameShadow(Qwt.QwtDial.Plain)
        self.needle.setWidth(15)
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

        self.title_label = overlayLabel(self, "Elevation")
        self.overlayDial = overlayElQwtDial()
        self.parent_grid.addWidget(self,0,0,15,15)
        self.parent_grid.addWidget(self.overlayDial,0,0,15,15)

        self.cur_label = overlayLabel(self, "Current", 15, 255,0,0,False, True)
        self.cur_label.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignBottom)
        self.parent_grid.addWidget(self.cur_label,12,0,1,1)

        self.tar_label = overlayLabel(self, "Target", 15, 0,0,255,False,True)
        self.tar_label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignBottom)
        self.parent_grid.addWidget(self.tar_label,12,14,1,1)

        self.cur_lcd = overlayLCD(self, True)
        self.parent_grid.addWidget(self.cur_lcd,13,0,2,1)
        
        self.tar_lcd = overlayLCD(self, False)
        self.parent_grid.addWidget(self.tar_lcd,13,14,2,1)

    def set_cur_el(self, el):
        self.setValue(el)
        self.cur_lcd.display(el)

    def set_tar_el(self, el):
        self.overlayDial.setValue(el)
        self.tar_lcd.display(el)

class overlayElQwtDial(Qwt.QwtDial):
    def __init__(self):
        super(overlayElQwtDial, self).__init__()
        self.needle = Qwt.QwtDialSimpleNeedle(Qwt.QwtDialSimpleNeedle.Ray, 1, QtGui.QColor(0,0,255))
        self.setOrigin(180)
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

    def set_el(self, el):
        self.setValue(el)
