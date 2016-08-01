#!/usr/bin/env python
#version 2.1

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

class el_QwtDial(Qwt.QwtDial):
    def __init__(self, parent=None):
        super(el_QwtDial, self).__init__(parent)
        self.parent = parent
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

        self.overlayDial = overlayElQwtDial(self.parent)
        self.title_label = overlayLabel(self, "Elevation")

        grid = QtGui.QGridLayout()
        grid.setSpacing(0)
        grid.addWidget(self,0,0,1,1)
        grid.addWidget(self.overlayDial,0,0,1,1)
        grid.setRowStretch(0,1)
        self.parent.setLayout(grid)

    def set_cur_el(self, el):
        self.setValue(el)

    def set_tar_el(self, el):
        self.overlayDial.setValue(el)

class overlayElQwtDial(Qwt.QwtDial):
    def __init__(self, parent=None):
        super(overlayElQwtDial, self).__init__(parent)
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
