#!/usr/bin/env python

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import Qt
import PyQt4.Qwt5 as Qwt
import numpy as np

import sys

class main_widget(QtGui.QWidget):
    
    def __init__(self):
        super(main_widget, self).__init__()
        
        self.initUI()
        
    def initUI(self):
        
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
        self.grid.setColumnStretch(0,1)
        self.grid.setColumnStretch(1,2)

class funcube_tlm_gui(QtGui.QMainWindow):
    def __init__(self):
        super(funcube_tlm_gui, self).__init__()
        self.resize(1500,1000)
        self.move(50,50)
        self.setWindowTitle('FunCube Telemetry Decoder')
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

        self.show()
