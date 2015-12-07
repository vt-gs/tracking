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

class MainWindow(QtGui.QWidget):
    def __init__(self, ip, port):
        QtGui.QMainWindow.__init__(self)

        self.resize(700, 700)
        self.setFixedWidth(700)
        self.setFixedHeight(500)
        self.setWindowTitle('VTGS Tracking GUI v1.0')
        self.setContentsMargins(0,0,0,0)
        
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

        self.ssid = 'VUL'

        self.initUI()
        self.autoQuery_cb.setCheckState(QtCore.Qt.Checked)
        self.darken()
        self.setFocus()

    def initUI(self):
        self.initFrames()
        self.initAzimuth()
        self.initElevation()
        self.initControls()
        self.initSSID()
        self.connectSignals()
    
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

        self.queryButton.clicked.connect(self.queryButtonEvent) 
        self.stopButton.clicked.connect(self.stopButtonEvent) 
        self.homeButton.clicked.connect(self.homeButtonEvent)
        self.updateButton.clicked.connect(self.updateButtonEvent)  
        self.autoQuery_cb.stateChanged.connect(self.catchAutoQueryEvent)

        self.vul_rb.clicked.connect(self.updateSSIDButtonEvent)
        self.dish_3m0_rb.clicked.connect(self.updateSSIDButtonEvent)
        self.dish_4m5_rb.clicked.connect(self.updateSSIDButtonEvent)
        self.wx_rb.clicked.connect(self.updateSSIDButtonEvent)

        QtCore.QObject.connect(self.updateTimer, QtCore.SIGNAL('timeout()'), self.queryButtonEvent)
        QtCore.QObject.connect(self.update_rate_le, QtCore.SIGNAL('editingFinished()'), self.updateRate)

    def updateSSIDButtonEvent(self, e):
        #vul_rb_state = self.vul_rb.isChecked
        #dish_3m0_rb_state = self.vul_rb.isChecked
        #dish_4m5_rb_state = self.vul_rb.isChecked
        #wx_rb_state = self.vul_rb.isChecked
        
        if self.vul_rb.isChecked() == True:
            self.ssid = 'VUL'
            self.vul_rb.setStyleSheet("QRadioButton { font-size: 14px; background-color:rgb(255,102,0); color:rgb(255,255,255)}")
            self.dish_3m0_rb.setStyleSheet("QRadioButton { font-size: 14px; background-color:rgb(102,0,0); color:rgb(255,255,255)}")
            self.dish_4m5_rb.setStyleSheet("QRadioButton { font-size: 14px; background-color:rgb(102,0,0); color:rgb(255,255,255)}")
            self.wx_rb.setStyleSheet("QRadioButton { font-size: 14px; background-color:rgb(102,0,0); color:rgb(255,255,255)}")
        elif self.dish_3m0_rb.isChecked() == True:
            self.ssid = '3M0'
            self.vul_rb.setStyleSheet("QRadioButton { font-size: 14px; background-color:rgb(102,0,0); color:rgb(255,255,255)}")
            self.dish_3m0_rb.setStyleSheet("QRadioButton { font-size: 14px; background-color:rgb(255,102,0); color:rgb(255,255,255)}")
            self.dish_4m5_rb.setStyleSheet("QRadioButton { font-size: 14px; background-color:rgb(102,0,0); color:rgb(255,255,255)}")
            self.wx_rb.setStyleSheet("QRadioButton { font-size: 14px; background-color:rgb(102,0,0); color:rgb(255,255,255)}")
        elif self.dish_4m5_rb.isChecked() == True:
            self.ssid = '4M5'
            self.vul_rb.setStyleSheet("QRadioButton { font-size: 14px; background-color:rgb(102,0,0); color:rgb(255,255,255)}")
            self.dish_3m0_rb.setStyleSheet("QRadioButton { font-size: 14px; background-color:rgb(102,0,0); color:rgb(255,255,255)}")
            self.dish_4m5_rb.setStyleSheet("QRadioButton { font-size: 14px; background-color:rgb(255,102,0); color:rgb(255,255,255)}")
            self.wx_rb.setStyleSheet("QRadioButton { font-size: 14px; background-color:rgb(102,0,0); color:rgb(255,255,255)}")
        elif self.wx_rb.isChecked() == True:
            self.ssid = 'WX'
            self.vul_rb.setStyleSheet("QRadioButton { font-size: 14px; background-color:rgb(102,0,0); color:rgb(255,255,255)}")
            self.dish_3m0_rb.setStyleSheet("QRadioButton { font-size: 14px; background-color:rgb(102,0,0); color:rgb(255,255,255)}")
            self.dish_4m5_rb.setStyleSheet("QRadioButton { font-size: 14px; background-color:rgb(102,0,0); color:rgb(255,255,255)}")
            self.wx_rb.setStyleSheet("QRadioButton { font-size: 14px; background-color:rgb(255,102,0); color:rgb(255,255,255)}")
        #print vul_rb_state, dish_3m0_rb_state, dish_4m5_rb_state, wx_rb_state
        print self.ssid

        #self.callback.updateSSID(self.ssid)



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
        valid, cur_az, cur_el = self.callback.get_status()
        if valid != False:
            self.cur_az = cur_az
            self.cur_el = cur_el
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
            print self.getTimeStampGMT() + "GUI|  Started Auto Update, Interval: " + str(self.update_rate) + " [ms]"
        else:
            self.updateTimer.stop()
            print self.getTimeStampGMT() + "GUI|  Stopped Auto Update"

    def updateRate(self):
        self.update_rate = float(self.update_rate_le.text()) * 1000.0
        self.updateTimer.setInterval(self.update_rate)
        print self.getTimeStampGMT() + "GUI|  Updated Rate Interval to " + str(self.update_rate) + " [ms]"

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

    def initSSID(self):
        self.vul_rb = QtGui.QRadioButton("VHF/UHF/L-Band Subsystem", self)  #Select VUL Antenna Subsystem
        self.vul_rb.setStyleSheet("QRadioButton { font-size: 14px; \
                                                    background-color:rgb(255,102,0); \
                                                    selection-background-color:rgb(255,0,0); \
                                                    color:rgb(255,255,255); }")
        self.vul_rb.setChecked(True)

        self.dish_3m0_rb = QtGui.QRadioButton("3.0m Dish Subsystem", self)  #Select 3.0m Dish Antenna Subsystem
        self.dish_3m0_rb.setStyleSheet("QRadioButton { font-size: 14px; \
                                                    background-color:rgb(102,0,0); \
                                                    color:rgb(255,255,255); }")

        self.dish_4m5_rb = QtGui.QRadioButton("4.5m Dish Subsystem", self)  #Select 4.5m Dish Antenna Subsystem
        self.dish_4m5_rb.setStyleSheet("QRadioButton { font-size: 14px; \
                                                    background-color:rgb(102,0,0); \
                                                    color:rgb(255,255,255); }")
        self.wx_rb = QtGui.QRadioButton("NOAA WX-Sat Subsystem", self)  #Select NOAA WX-Sat Antenna Subsystem
        self.wx_rb.setStyleSheet("QRadioButton { font-size: 14px; \
                                                    background-color:rgb(102,0,0); \
                                                    color:rgb(255,255,255); }")


        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.vul_rb)
        vbox.addWidget(self.dish_3m0_rb)
        vbox.addWidget(self.dish_4m5_rb)
        vbox.addWidget(self.wx_rb)

        self.ssid_fr.setLayout(vbox)

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

    def initElevation(self):
        self.el_compass = el_QwtDial(self.el_fr)
        x = 172; y = 350; w = 50; s = 4; h = 25
        self.elPlusPtOneButton = QtGui.QPushButton(self.el_fr)
        self.elPlusPtOneButton.setText("+0.1")
        self.elPlusPtOneButton.setGeometry(x,y,w,h)

        
        self.elPlusOneButton = QtGui.QPushButton(self.el_fr)
        self.elPlusOneButton.setText("+1.0")
        self.elPlusOneButton.setGeometry(x+s+w,y,w,h)

        self.elPlusTenButton = QtGui.QPushButton(self.el_fr)
        self.elPlusTenButton.setText("+10.0")
        self.elPlusTenButton.setGeometry(x+(2*s)+(2*w),y,w,h)

        self.elMinusPtOneButton = QtGui.QPushButton(self.el_fr)
        self.elMinusPtOneButton.setText("-0.1")
        self.elMinusPtOneButton.setGeometry(x-s-w,y,w,h)

        self.elMinusOneButton = QtGui.QPushButton(self.el_fr)
        self.elMinusOneButton.setText("-1.0")
        self.elMinusOneButton.setGeometry(x-(2*s)-(2*w),y,w,h)

        self.elMinusTenButton = QtGui.QPushButton(self.el_fr)
        self.elMinusTenButton.setText("-10.0")
        self.elMinusTenButton.setGeometry(x-(3*s)-(3*w),y,w,h)

        self.elTextBox = QtGui.QLineEdit(self.el_fr)
        self.elTextBox.setText("000.0")
        self.elTextBox.setInputMask("000.0;")
        self.elTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.elTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.elTextBox.setMaxLength(6)
        self.elTextBox.setGeometry(145,320,60,25)

    def initAzimuth(self):
        #geo = self.az_fr.frameRect()
        #print geo.x, geo.y, geo.width, geo.height
        self.az_compass = az_QwtDial(self.az_fr)
        x = 172; y = 350; w = 50; s = 4; h = 25
        self.azPlusPtOneButton = QtGui.QPushButton(self.az_fr)
        self.azPlusPtOneButton.setText("+0.1")
        self.azPlusPtOneButton.setGeometry(x,y,w,h)

        self.azPlusOneButton = QtGui.QPushButton(self.az_fr)
        self.azPlusOneButton.setText("+1.0")
        self.azPlusOneButton.setGeometry(x+s+w,y,w,h)

        self.azPlusTenButton = QtGui.QPushButton(self.az_fr)
        self.azPlusTenButton.setText("+10.0")
        self.azPlusTenButton.setGeometry(x+(2*s)+(2*w),y,w,h)

        self.azMinusPtOneButton = QtGui.QPushButton(self.az_fr)
        self.azMinusPtOneButton.setText("-0.1")
        self.azMinusPtOneButton.setGeometry(x-s-w,y,w,h)

        self.azMinusOneButton = QtGui.QPushButton(self.az_fr)
        self.azMinusOneButton.setText("-1.0")
        self.azMinusOneButton.setGeometry(x-(2*s)-(2*w),y,w,h)

        self.azMinusTenButton = QtGui.QPushButton(self.az_fr)
        self.azMinusTenButton.setText("-10.0")
        self.azMinusTenButton.setGeometry(x-(3*s)-(3*w),y,w,h)

        self.azTextBox = QtGui.QLineEdit(self.az_fr)
        self.azTextBox.setText("180.0")
        self.azTextBox.setInputMask("#000.0;")
        self.azTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.azTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.azTextBox.setMaxLength(6)
        self.azTextBox.setGeometry(145,320,60,25)

    def initFrames(self):
        self.az_fr = QtGui.QFrame(self)
        self.az_fr.setFrameShape(QtGui.QFrame.StyledPanel)
        self.az_fr.setFixedWidth(340)
        self.az_fr.setFixedHeight(380)

        self.el_fr = QtGui.QFrame(self)
        self.el_fr.setFrameShape(QtGui.QFrame.StyledPanel)
        self.el_fr.setFixedWidth(340)
        self.el_fr.setFixedHeight(380)

        self.button_fr = QtGui.QFrame(self)
        self.button_fr.setFrameShape(QtGui.QFrame.StyledPanel)
        self.button_fr.setFixedWidth(340)
        self.button_fr.setFixedHeight(100)

        self.ssid_fr = QtGui.QFrame(self)
        self.ssid_fr.setFrameShape(QtGui.QFrame.StyledPanel)
        self.ssid_fr.setFixedWidth(340)
        self.ssid_fr.setFixedHeight(100)

        vbox = QtGui.QVBoxLayout()
        hbox1 = QtGui.QHBoxLayout()
        hbox2 = QtGui.QHBoxLayout()

        hbox1.addWidget(self.az_fr)
        hbox1.addWidget(self.el_fr)

        hbox2.addWidget(self.ssid_fr)
        hbox2.addWidget(self.button_fr)        

        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        
        self.setLayout(vbox)

    def darken(self):
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background,QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.WindowText,QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Text,QtCore.Qt.white)
        self.setPalette(palette)

    def getTimeStampGMT(self):
        return str(date.utcnow()) + " GMT | "

