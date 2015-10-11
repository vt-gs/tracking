#!/usr/bin/env python

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import Qt

import PyQt4.Qwt5 as Qwt
import numpy as np
from datetime import datetime as date
import sys
from az_QwtDial import *
from el_QwtDial import *
import time

class main_widget(QtGui.QWidget):
    def __init__(self):
        super(main_widget, self).__init__()
        self.initUI()
       
    def initUI(self):
        
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
        #self.grid.setColumnStretch(0,1)
        #self.grid.setColumnStretch(1,2)

class MainWindow(QtGui.QMainWindow):
    def __init__(self, ip, port):
        #QtGui.QMainWindow.__init__(self)
        super(MainWindow, self).__init__()
        self.resize(700, 550)
        self.setMinimumWidth(600)
        self.setMaximumWidth(850)
        self.setMinimumHeight(500)
        self.setMaximumHeight(800)
        self.setWindowTitle('MD01 Controller v1.2')
        self.setContentsMargins(0,0,0,0)
        self.main_window = main_widget()
        self.setCentralWidget(self.main_window)

        self.ip = ip
        self.port = port

        self.cur_az = 0
        self.tar_az = 0
        self.cur_el = 0
        self.tar_el = 0
        self.home_az = 0.0
        self.home_el = 0.0

        self.callback    = None   #Callback accessor for tracking control
        self.connected   = False  #Status of TCP/IP connection to MD-01
        self.update_rate = 250    #Feedback Query Auto Update Interval in milliseconds

        self.statusBar().showMessage("Disconnected")

        self.initUI()
        self.darken()
        self.setFocus()

    def initUI(self):
        #self.grid = QtGui.QGridLayout()
        #self.setLayout(self.grid)
        self.initFrames()
        self.Init_Tabs()
        self.initAzimuth()
        self.initElevation()
        #self.initControls()
        #self.initMotorCtrl()
        #self.initNet()
        #self.connectSignals()
        self.show()
    
    def Init_Tabs(self):
        self.tabs = QtGui.QTabWidget()
        self.tabs.setTabPosition(QtGui.QTabWidget.South)
        
        self.main_tab = QtGui.QWidget()	
        self.main_tab.grid = QtGui.QGridLayout()
        self.tabs.addTab(self.main_tab,"Main")
        
        self.config_tab = QtGui.QWidget()	
        self.config_tab.grid = QtGui.QGridLayout()
        self.tabs.addTab(self.config_tab,"Configuration")

        self.net_tab = QtGui.QWidget()	
        self.net_tab.grid = QtGui.QGridLayout()
        self.tabs.addTab(self.net_tab,"Network")
        
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background,QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.Foreground,QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.WindowText,QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.Text,QtCore.Qt.white)
        #self.main_tab.setPalette(palette)
        self.tabs.setPalette(palette)

        self.main_window.grid.addWidget(self.tabs,13,0,5,20)

    def initFrames(self):
        self.az_dial_fr = QtGui.QFrame(self)
        self.az_dial_fr.setFrameShape(QtGui.QFrame.StyledPanel)
        self.az_dial_fr_grid = QtGui.QGridLayout()
        self.az_dial_fr.setLayout(self.az_dial_fr_grid)

        self.az_ctrl_fr = QtGui.QFrame(self)
        self.az_ctrl_fr.setFrameShape(QtGui.QFrame.StyledPanel)

        self.el_dial_fr = QtGui.QFrame(self)
        self.el_dial_fr.setFrameShape(QtGui.QFrame.StyledPanel)
        self.el_dial_fr_grid = QtGui.QGridLayout()
        self.el_dial_fr.setLayout(self.el_dial_fr_grid)

        self.el_ctrl_fr = QtGui.QFrame(self)
        self.el_ctrl_fr.setFrameShape(QtGui.QFrame.StyledPanel)

        self.main_window.grid.addWidget(self.az_dial_fr,0,0,10,10)
        self.main_window.grid.addWidget(self.az_ctrl_fr,10,0,1,10)
        self.main_window.grid.addWidget(self.el_dial_fr,0,10,10,10)
        self.main_window.grid.addWidget(self.el_ctrl_fr,10,10,1,10)

    def initElevation(self):
        self.el_compass = el_QwtDial(self.el_dial_fr_grid)

        self.elPlusPtOneButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elPlusPtOneButton.setText("+0.1")
        self.elPlusPtOneButton.setFixedWidth(50)
        
        self.elPlusOneButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elPlusOneButton.setText("+1.0")
        self.elPlusOneButton.setFixedWidth(50)

        self.elPlusTenButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elPlusTenButton.setText("+10.0")
        self.elPlusTenButton.setFixedWidth(50)

        self.elMinusPtOneButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elMinusPtOneButton.setText("-0.1")
        self.elMinusPtOneButton.setFixedWidth(50)

        self.elMinusOneButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elMinusOneButton.setText("-1.0")
        self.elMinusOneButton.setFixedWidth(50)

        self.elMinusTenButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elMinusTenButton.setText("-10.0")
        self.elMinusTenButton.setFixedWidth(50)

        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.elMinusTenButton)
        hbox1.addWidget(self.elMinusOneButton)
        hbox1.addWidget(self.elMinusPtOneButton)
        hbox1.addWidget(self.elPlusPtOneButton)
        hbox1.addWidget(self.elPlusOneButton)
        hbox1.addWidget(self.elPlusTenButton)
        self.el_ctrl_fr.setLayout(hbox1)

        #self.elTextBox = QtGui.QLineEdit(self.el_dial_fr)
        #self.elTextBox.setText("000.0")
        #self.elTextBox.setInputMask("000.0;")
        #self.elTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        #self.elTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        #self.elTextBox.setMaxLength(6)
        #self.elTextBox.setGeometry(140,320,60,25)

    def initAzimuth(self):
        self.az_compass = az_QwtDial(self.az_dial_fr_grid)

        self.azPlusPtOneButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azPlusPtOneButton.setText("+0.1")
        self.azPlusPtOneButton.setFixedWidth(50)

        self.azPlusOneButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azPlusOneButton.setText("+1.0")
        self.azPlusOneButton.setFixedWidth(50)

        self.azPlusTenButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azPlusTenButton.setText("+10.0")
        self.azPlusTenButton.setFixedWidth(50)

        self.azMinusPtOneButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azMinusPtOneButton.setText("-0.1")
        self.azMinusPtOneButton.setFixedWidth(50)

        self.azMinusOneButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azMinusOneButton.setText("-1.0")
        self.azMinusOneButton.setFixedWidth(50)

        self.azMinusTenButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azMinusTenButton.setText("-10.0")
        self.azMinusTenButton.setFixedWidth(50)

        #self.az_ctrl_fr_grid.addWidget(self.azMinusTenButton,0,0,1,1)
        #self.az_ctrl_fr_grid.addWidget(self.azMinusOneButton,0,1,1,1)
        #self.az_ctrl_fr_grid.addWidget(self.azMinusPtOneButton,0,2,1,1)
        #self.az_ctrl_fr_grid.addWidget(self.azPlusPtOneButton,0,3,1,1)
        #self.az_ctrl_fr_grid.addWidget(self.azPlusOneButton,0,4,1,1)
        #self.az_ctrl_fr_grid.addWidget(self.azPlusTenButton,0,5,1,1)

        #self.azTextBox = QtGui.QLineEdit(self.az_ctrl_fr)
        #self.azTextBox.setText("180.0")
        #self.azTextBox.setInputMask("#000.0;")
        #self.azTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        #self.azTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        #self.azTextBox.setMaxLength(6)
        #self.azTextBox.setGeometry(140,320,60,25)

        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.azMinusTenButton)
        hbox1.addWidget(self.azMinusOneButton)
        hbox1.addWidget(self.azMinusPtOneButton)
        hbox1.addWidget(self.azPlusPtOneButton)
        hbox1.addWidget(self.azPlusOneButton)
        hbox1.addWidget(self.azPlusTenButton)
        self.az_ctrl_fr.setLayout(hbox1)


























    def setCallback(self, callback):
        self.callback = callback

    def connectSignals(self):
        self.azPlusPtOneButton.clicked.connect(self.azPlusPtOneButtonClicked) 
        self.azPlusOneButton.clicked.connect(self.azPlusOneButtonClicked) 
        self.azPlusTenButton.clicked.connect(self.azPlusTenButtonClicked) 
        self.azMinusPtOneButton.clicked.connect(self.azMinusPtOneButtonClicked) 
        self.azMinusOneButton.clicked.connect(self.azMinusOneButtonClicked) 
        self.azMinusTenButton.clicked.connect(self.azMinusTenButtonClicked) 
        self.azTextBox.returnPressed.connect(self.azTextBoxReturnPressed)

        self.elPlusPtOneButton.clicked.connect(self.elPlusPtOneButtonClicked) 
        self.elPlusOneButton.clicked.connect(self.elPlusOneButtonClicked) 
        self.elPlusTenButton.clicked.connect(self.elPlusTenButtonClicked) 
        self.elMinusPtOneButton.clicked.connect(self.elMinusPtOneButtonClicked) 
        self.elMinusOneButton.clicked.connect(self.elMinusOneButtonClicked) 
        self.elMinusTenButton.clicked.connect(self.elMinusTenButtonClicked) 
        self.elTextBox.returnPressed.connect(self.elTextBoxReturnPressed)

        self.connectButton.clicked.connect(self.connectButtonEvent)
        self.queryButton.clicked.connect(self.queryButtonEvent) 
        self.stopButton.clicked.connect(self.stopButtonEvent) 
        self.homeButton.clicked.connect(self.homeButtonEvent)
        self.updateButton.clicked.connect(self.updateButtonEvent)  
        self.autoQuery_cb.stateChanged.connect(self.catchAutoQueryEvent)

        QtCore.QObject.connect(self.updateTimer, QtCore.SIGNAL('timeout()'), self.queryButtonEvent)
        QtCore.QObject.connect(self.update_rate_le, QtCore.SIGNAL('editingFinished()'), self.updateRate)
        QtCore.QObject.connect(self.ipAddrTextBox, QtCore.SIGNAL('editingFinished()'), self.updateIPAddress)
        QtCore.QObject.connect(self.portTextBox, QtCore.SIGNAL('editingFinished()'), self.updatePort)

    def updateButtonEvent(self):
        self.updateAzimuth()
        self.updateElevation()

    def homeButtonEvent(self):
        self.tar_az = self.home_az
        self.tar_el = self.home_el
        self.updateAzimuth()
        self.updateElevation()

    def stopButtonEvent(self):
        status, self.cur_az, self.cur_el = self.callback.set_stop()
        if status != -1:
            self.az_compass.set_cur_az(self.cur_az)
            self.el_compass.set_cur_el(self.cur_el)

    def queryButtonEvent(self):
        status, self.cur_az, self.cur_el = self.callback.get_status()
        if status != -1:
            self.az_compass.set_cur_az(self.cur_az)
            self.el_compass.set_cur_el(self.cur_el)
        else:
            self.autoQuery_cb.setCheckState(QtCore.Qt.Unchecked)

    def connectButtonEvent(self):
        if (not self.connected):  #Not connected, attempt to connect
            self.connected = self.callback.connect()
            if (self.connected): 
                self.connectButton.setText('Disconnect')
                self.net_label.setText("Connected")
                self.net_label.setStyleSheet("QLabel {  font-weight:bold; color:rgb(0,255,0) ; }")
                self.ipAddrTextBox.setStyleSheet("QLineEdit {background-color:rgb(225,225,225); color:rgb(0,0,0);}")
                self.portTextBox.setStyleSheet("QLineEdit {background-color:rgb(225,225,225); color:rgb(0,0,0);}")
                self.ipAddrTextBox.setEnabled(False)
                self.portTextBox.setEnabled(False)
        else:
            self.connected = self.callback.disconnect()
            if (not self.connected): 
                self.connectButton.setText('Connect')
                self.net_label.setText("Disconnected")
                self.net_label.setStyleSheet("QLabel {  font-weight:bold; color:rgb(255,0,0) ; }")
                self.ipAddrTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
                self.portTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
                self.ipAddrTextBox.setEnabled(True)
                self.portTextBox.setEnabled(True)

    def catchAutoQueryEvent(self, state):
        CheckState = (state == QtCore.Qt.Checked)
        if CheckState == True:  
            self.updateTimer.start()
            print self.getTimeStampGMT() + "GUI  | Started Auto Update, Interval: " + str(self.update_rate) + " [ms]"
        else:
            self.updateTimer.stop()
            print self.getTimeStampGMT() + "GUI  | Stopped Auto Update"

    def updateRate(self):
        self.update_rate = float(self.update_rate_le.text()) * 1000.0
        self.updateTimer.setInterval(self.update_rate)
        print self.getTimeStampGMT() + "GUI  | Updated Rate Interval to " + str(self.update_rate) + " [ms]"

    def updateIPAddress(self):
        self.ip = self.ipAddrTextBox.text()

    def updatePort(self):
        self.port = self.portTextBox.text()

    def azTextBoxReturnPressed(self):
        self.tar_az = float(self.azTextBox.text())
        self.updateAzimuth()
    
    def azPlusPtOneButtonClicked(self):
        self.tar_az = self.tar_az + 0.1
        self.updateAzimuth()

    def azPlusOneButtonClicked(self):
        self.tar_az = self.tar_az + 1
        self.updateAzimuth()

    def azPlusTenButtonClicked(self):
        self.tar_az = self.tar_az + 10
        self.updateAzimuth()

    def azMinusPtOneButtonClicked(self):
        self.tar_az = self.tar_az - 0.1
        self.updateAzimuth()

    def azMinusOneButtonClicked(self):
        self.tar_az = self.tar_az - 1
        self.updateAzimuth()

    def azMinusTenButtonClicked(self):
        self.tar_az = self.tar_az - 10
        self.updateAzimuth()

    def updateAzimuth(self):
        if self.tar_az < -180: 
            self.tar_az = -180
            self.azTextBox.setText(str(self.tar_az))
        if self.tar_az > 540: 
            self.tar_az = 540
            self.azTextBox.setText(str(self.tar_az))
        self.az_compass.set_tar_az(self.tar_az)
        self.callback.set_position(self.tar_az, self.tar_el)

    def elTextBoxReturnPressed(self):
        self.tar_el = float(self.elTextBox.text())
        self.updateElevation()
    
    def elPlusPtOneButtonClicked(self):
        self.tar_el = self.tar_el + 0.1
        self.updateElevation()

    def elPlusOneButtonClicked(self):
        self.tar_el = self.tar_el + 1
        self.updateElevation()

    def elPlusTenButtonClicked(self):
        self.tar_el = self.tar_el + 10
        self.updateElevation()

    def elMinusPtOneButtonClicked(self):
        self.tar_el = self.tar_el - 0.1
        self.updateElevation()

    def elMinusOneButtonClicked(self):
        self.tar_el = self.tar_el - 1
        self.updateElevation()

    def elMinusTenButtonClicked(self):
        self.tar_el = self.tar_el - 10
        self.updateElevation()

    def updateElevation(self):
        if self.tar_el < 0: 
            self.tar_el = 0
            self.elTextBox.setText(str(self.tar_el))
        if self.tar_el > 180: 
            self.tar_el = 180
            self.elTextBox.setText(str(self.tar_el))
        self.el_compass.set_tar_el(self.tar_el)
        self.callback.set_position(self.tar_az, self.tar_el)

    def initNet(self):
        self.ipAddrTextBox = QtGui.QLineEdit()
        self.ipAddrTextBox.setText(self.ip)
        self.ipAddrTextBox.setInputMask("000.000.000.000;")
        self.ipAddrTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.ipAddrTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.ipAddrTextBox.setMaxLength(15)

        self.portTextBox = QtGui.QLineEdit()
        self.portTextBox.setText(str(self.port))
        self.port_validator = QtGui.QIntValidator()
        self.port_validator.setRange(0,65535)
        self.portTextBox.setValidator(self.port_validator)
        self.portTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.portTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.portTextBox.setMaxLength(5)
        self.portTextBox.setFixedWidth(50)

        label = QtGui.QLabel('Status:')
        label.setAlignment(QtCore.Qt.AlignRight)
        self.net_label = QtGui.QLabel('Disconnected')
        self.net_label.setAlignment(QtCore.Qt.AlignLeft)
        self.net_label.setFixedWidth(150)

        self.connectButton = QtGui.QPushButton("Connect")
        self.net_label.setStyleSheet("QLabel {font-weight:bold; color:rgb(255,0,0);}")

        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.ipAddrTextBox)
        hbox1.addWidget(self.portTextBox)

        hbox2 = QtGui.QHBoxLayout()
        hbox2.addWidget(label)
        hbox2.addWidget(self.net_label)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addWidget(self.connectButton)
        vbox.addLayout(hbox2)

        self.net_fr.setLayout(vbox)

    def initControls(self):
        self.updateButton = QtGui.QPushButton("Update")
        self.queryButton  = QtGui.QPushButton("Query")
        self.homeButton   = QtGui.QPushButton("Home")
        self.stopButton   = QtGui.QPushButton("STOP!")
        
        self.autoQuery_cb = QtGui.QCheckBox("Auto Query", self)  #Automatically update ADC voltages checkbox option
        self.autoQuery_cb.setStyleSheet("QCheckBox { font-size: 12px; \
                                                    background-color:rgb(0,0,0); \
                                                    color:rgb(255,255,255); }")

        self.update_rate_le = QtGui.QLineEdit()
        self.update_rate_le.setText("0.25")
        self.update_val = QtGui.QDoubleValidator()
        self.update_rate_le.setValidator(self.update_val)
        self.update_rate_le.setEchoMode(QtGui.QLineEdit.Normal)
        self.update_rate_le.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.update_rate_le.setMaxLength(4)
        self.update_rate_le.setFixedWidth(50)

        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.autoQuery_cb)
        hbox1.addWidget(self.update_rate_le)

        hbox2 = QtGui.QHBoxLayout()
        hbox2.addWidget(self.updateButton)
        hbox2.addWidget(self.queryButton)
        hbox2.addWidget(self.homeButton)

        hbox3 = QtGui.QHBoxLayout()
        hbox3.addWidget(self.stopButton)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)

        self.button_fr.setLayout(vbox)

        self.updateTimer = QtCore.QTimer(self)
        self.updateTimer.setInterval(self.update_rate)

    def initMotorCtrl(self):
        self.UpLeftButton = QtGui.QPushButton("U+L")
        self.UpButton = QtGui.QPushButton("Up")
        self.UpRightButton = QtGui.QPushButton("U+R")
        self.LeftButton = QtGui.QPushButton("Left")
        self.StopButton = QtGui.QPushButton("STOP!")
        self.RightButton = QtGui.QPushButton("Right")
        self.DnLeftButton = QtGui.QPushButton("D+L")
        self.DownButton = QtGui.QPushButton("Down")
        self.DnRightButton = QtGui.QPushButton("D+R")

        vbox = QtGui.QVBoxLayout()
        hbox1 = QtGui.QHBoxLayout()
        hbox2 = QtGui.QHBoxLayout()
        hbox3 = QtGui.QHBoxLayout()

        hbox1.addWidget(self.UpLeftButton)
        hbox1.addWidget(self.UpButton)
        hbox1.addWidget(self.UpRightButton)

        hbox2.addWidget(self.LeftButton)
        hbox2.addWidget(self.StopButton)
        hbox2.addWidget(self.RightButton)

        hbox3.addWidget(self.DnLeftButton)
        hbox3.addWidget(self.DownButton)
        hbox3.addWidget(self.DnRightButton)

        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)

        self.ctrl_fr.setLayout(vbox)

    



    def darken(self):
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background,QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.WindowText,QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.Text,QtCore.Qt.white)
        self.setPalette(palette)

    def getTimeStampGMT(self):
        return str(date.utcnow()) + " GMT | "

