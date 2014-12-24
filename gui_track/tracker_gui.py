#!/usr/bin/env python

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import Qt
import PyQt4.Qwt5 as Qwt
import numpy as np

import sys
import time

class main_widget(QtGui.QWidget):
    
    def __init__(self):
        super(main_widget, self).__init__()
        
        self.initUI()
        
    def initUI(self):
        
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
        self.grid.setColumnStretch(0,1)
        self.grid.setColumnStretch(1,2)

class tracker_main_gui(QtGui.QMainWindow):
    def __init__(self):
        super(tracker_main_gui, self).__init__()
        self.resize(1500,1000)
        self.move(50,50)
        self.setWindowTitle('VTGS Tracking GUI')
        self.setAutoFillBackground(True)
        #self.ants_static_labels = []
        self.main_window = main_widget()
        self.initUI()
        
    def initUI(self): 
        self.setCentralWidget(self.main_window)
        exitAction = QtGui.QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(QtGui.qApp.quit)

        exportAction = QtGui.QAction('Export', self)
        exportAction.setShortcut('Ctrl+E')
        exportAction.triggered.connect(QtGui.qApp.quit)

        menubar = self.menuBar()
        self.fileMenu = menubar.addMenu('&File')
        self.fileMenu.addAction(exitAction)
        self.fileMenu.addAction(exportAction)
        
        az_compass = compass()
        self.main_window.grid.addWidget(az_compass, 0,0,1,1)
        self.show()
        
        time.sleep(1)
        az_compass.set_value(90)
        
        time.sleep(1)
        az_compass.set_value(135)

        

class compass(Qwt.QwtCompass):
    def __init__(self, *args):
        Qwt.QwtCompass.__init__(self, *args)
        self.needle = needle(Qwt.QwtCompassMagnetNeedle.ThinStyle)
        #self.needle = needle2()
        #self.needle = needle3(Qwt.QwtCompassWindArrow.Style1)
        self.setNeedle(self.needle)
        self.setValue(20)

    def set_value(self, angle):
        self.setValue(angle)

class needle(Qwt.QwtCompassMagnetNeedle):
    def __init__(self, *args):
        Qwt.QwtCompassMagnetNeedle.__init__(self, *args)
        

class needle2(Qwt.QwtDialNeedle):
    def __init__(self, *args):
        Qwt.QwtDialNeedle.__init__(self, *args)
    
    def draw(self):
        pass

class needle3(Qwt.QwtCompassWindArrow):
    def __init__(self, *args):
        Qwt.QwtCompassWindArrow.__init__(self, *args)

    

