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
from gpredict import *

class main_widget(QtGui.QWidget):
    def __init__(self):
        super(main_widget, self).__init__()
        self.initUI()
       
    def initUI(self):
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)

class MainWindow(QtGui.QMainWindow):
    def __init__(self, ip, port):
        #QtGui.QMainWindow.__init__(self)
        super(MainWindow, self).__init__()
        self.resize(1000, 525)
        self.setMinimumWidth(800)
        #self.setMaximumWidth(900)
        self.setMinimumHeight(450)
        #self.setMaximumHeight(700)
        self.setWindowTitle('VTGS Tracking GUI v2.0')
        self.setContentsMargins(0,0,0,0)
        self.main_window = main_widget()
        self.setCentralWidget(self.main_window)

        self.ip = ip
        self.port = port

        self.cur_az = 0
        self.tar_az = 0
        self.cur_el = 0
        self.tar_el = 0
        self.pred_az = 0.0
        self.pred_el = 0.0
        self.home_az = 0.0
        self.home_el = 0.0

        self.callback    = None   #Callback accessor for tracking control
        self.update_rate = 250    #Feedback Query Auto Update Interval in milliseconds

        self.gpredict  = None     #Callback accessor for gpredict thread control
        self.pred_conn_stat = 0   #Gpredict Connection Status, 0=Disconnected, 1=Listening, 2=Connected
        self.autoTrack = False    #auto track mode, True = Auto, False = Manual

        self.statusBar().showMessage("| Disconnected | Manual | Current Az: 000.0 | Current El: 000.0 |")

        self.initUI()
        self.darken()
        self.setFocus()

    def initUI(self):
        self.initTabControl()
        self.initMainTab()
        self.initCalTab()
        self.initTimers()

        self.connectSignals()
        self.show()

    def initTimers(self):
        self.updateTimer = QtCore.QTimer(self)
        #self.updateTimer.setInterval(self.update_rate)
        self.updateTimer.start(self.update_rate)

        #Timer used to Poll the GPredict Server thread for updates
        self.predictTimer = QtCore.QTimer(self)
        self.predictTimer.setInterval(self.update_rate)

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

        self.predictButton.clicked.connect(self.predictButtonEvent)
        self.queryButton.clicked.connect(self.queryButtonEvent) 
        self.StopButton.clicked.connect(self.stopButtonEvent) 
        self.homeButton.clicked.connect(self.homeButtonEvent)
        self.updateButton.clicked.connect(self.updateButtonEvent)  
        self.autoQuery_cb.stateChanged.connect(self.catchAutoQueryEvent)

        QtCore.QObject.connect(self.updateTimer, QtCore.SIGNAL('timeout()'), self.queryButtonEvent)
        QtCore.QObject.connect(self.predictTimer, QtCore.SIGNAL('timeout()'), self.predictTimerEvent)
        QtCore.QObject.connect(self.fb_query_rate_le, QtCore.SIGNAL('editingFinished()'), self.updateRate)
        QtCore.QObject.connect(self.ipAddrTextBox, QtCore.SIGNAL('editingFinished()'), self.updateIPAddress)
        QtCore.QObject.connect(self.portTextBox, QtCore.SIGNAL('editingFinished()'), self.updatePort)
        self.ssidCombo.activated[int].connect(self.updateSSIDEvent)

    def setCallback(self, callback):
        self.callback = callback
    
    def setGpredictCallback(self, callback):
        self.gpredict = callback

    def predictTimerEvent(self):
        self.pred_conn_stat = self.gpredict.getConnectionStatus()
        if self.pred_conn_stat == 2:
            self.pred_az, self.pred_el = self.gpredict.getTargetAngles()
            self.gpredict.updateCurrentAngles(self.cur_az, self.cur_el)
            self.pred_az_lbl.setText(str(round(self.pred_az,1)))
            self.pred_el_lbl.setText(str(round(self.pred_el,1)))
            if self.autoTrack_cb.isChecked() == True:
                self.tar_az = round(self.pred_az, 1)
                self.tar_el = round(self.pred_el,1)
                self.updateAzimuth()
                self.updateElevation()
                self.callback.set_position(self.tar_az, self.tar_el)
        self.updatePredictStatus()

    def predictButtonEvent(self):
        if self.pred_conn_stat == 0:  #Disconnected, Start Connection Thread
            ip = self.ipAddrTextBox.text()
            port = int(self.portTextBox.text())
            self.gpredict = Gpredict_Thread(self, ip, port,1)
            self.gpredict.daemon = True
            self.gpredict.start()
            self.pred_conn_stat = 1 #listening
            self.updatePredictStatus()
            self.predictTimer.start()
        elif ((self.pred_conn_stat == 1) or (self.pred_conn_stat == 2)):
            self.gpredict.stop()
            self.gpredict.join()
            self.predictTimer.stop()
            self.pred_conn_stat = 0
            self.updatePredictStatus()

    def updatePredictStatus(self):
        if self.pred_conn_stat == 0: #Disconnected
            self.predictButton.setText('Connect')
            self.pred_status_lbl.setText("Disconnected")
            self.pred_status_lbl.setStyleSheet("QLabel {  font-weight:bold; color:rgb(255,0,0) ; }")
            self.ipAddrTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
            self.portTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
            self.ipAddrTextBox.setEnabled(True)
            self.portTextBox.setEnabled(True)
        elif self.pred_conn_stat == 1: #Listening
            self.predictButton.setText('Disconnect')
            self.pred_status_lbl.setText("Listening...")
            self.pred_status_lbl.setStyleSheet("QLabel {  font-weight:bold; color:rgb(255,255,0) ; }")
            self.ipAddrTextBox.setStyleSheet("QLineEdit {background-color:rgb(225,225,225); color:rgb(0,0,0);}")
            self.portTextBox.setStyleSheet("QLineEdit {background-color:rgb(225,225,225); color:rgb(0,0,0);}")
            self.ipAddrTextBox.setEnabled(False)
            self.portTextBox.setEnabled(False)
        elif self.pred_conn_stat == 2: #Connected
            self.predictButton.setText('Disconnect')
            self.pred_status_lbl.setText("Connected")
            self.pred_status_lbl.setStyleSheet("QLabel {  font-weight:bold; color:rgb(0,255,0) ; }")
            self.ipAddrTextBox.setStyleSheet("QLineEdit {background-color:rgb(225,225,225); color:rgb(0,0,0);}")
            self.portTextBox.setStyleSheet("QLineEdit {background-color:rgb(225,225,225); color:rgb(0,0,0);}")
            self.ipAddrTextBox.setEnabled(False)
            self.portTextBox.setEnabled(False)

    def updateSSIDEvent(self, idx):
        if   idx == 0: #VUL
            self.ssid = 'VUL'
        elif idx == 1: #3M0
            self.ssid = '3M0'
        elif idx == 2: #4M5
            self.ssid = '4M5'
        elif idx == 3: #WX
            self.ssid = 'WX'
        print self.utc_ts() + "GUI | Updated Subsystem ID: " + self.ssid
        self.callback.set_ssid(self.ssid)

    def updateButtonEvent(self):
        self.tar_az = float(self.azTextBox.text())
        self.tar_el = float(self.elTextBox.text())
        self.updateAzimuth()
        self.updateElevation()
        self.callback.set_position(self.tar_az, self.tar_el)

    def homeButtonEvent(self):
        self.tar_az = self.home_az
        self.tar_el = self.home_el
        self.updateAzimuth()
        self.updateElevation()
        self.callback.set_position(self.tar_az, self.tar_el)

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

    def catchAutoQueryEvent(self, state):
        CheckState = (state == QtCore.Qt.Checked)
        if CheckState == True:  
            self.updateTimer.start()
            print self.utc_ts() + "GUI | Started Auto Update, Interval: " + str(self.update_rate) + " [ms]"
        else:
            self.updateTimer.stop()
            print self.utc_ts() + "GUI | Stopped Auto Update"

    def updateRate(self):
        self.update_rate = float(self.fb_query_rate_le.text()) * 1000.0
        self.updateTimer.setInterval(self.update_rate)
        self.predictTimer.setInterval(self.update_rate)
        print self.utc_ts() + "GUI | Updated Rate Interval to " + str(self.update_rate) + " [ms]"

    def updateIPAddress(self):
        self.ip = self.ipAddrTextBox.text()

    def updatePort(self):
        self.port = self.portTextBox.text()

    def azTextBoxReturnPressed(self):
        self.tar_az = float(self.azTextBox.text())
        self.updateAzimuth()
        self.callback.set_position(self.tar_az, self.tar_el)
    
    def azPlusPtOneButtonClicked(self):
        self.tar_az = self.tar_az + 0.1
        self.updateAzimuth()
        self.callback.set_position(self.tar_az, self.tar_el)

    def azPlusOneButtonClicked(self):
        self.tar_az = self.tar_az + 1
        self.updateAzimuth()
        self.callback.set_position(self.tar_az, self.tar_el)

    def azPlusTenButtonClicked(self):
        self.tar_az = self.tar_az + 10
        self.updateAzimuth()
        self.callback.set_position(self.tar_az, self.tar_el)

    def azMinusPtOneButtonClicked(self):
        self.tar_az = self.tar_az - 0.1
        self.updateAzimuth()
        self.callback.set_position(self.tar_az, self.tar_el)

    def azMinusOneButtonClicked(self):
        self.tar_az = self.tar_az - 1
        self.updateAzimuth()
        self.callback.set_position(self.tar_az, self.tar_el)

    def azMinusTenButtonClicked(self):
        self.tar_az = self.tar_az - 10
        self.updateAzimuth()
        self.callback.set_position(self.tar_az, self.tar_el)

    def updateAzimuth(self):
        if self.tar_az < -180.0: 
            self.tar_az = -180.0
            self.azTextBox.setText(str(self.tar_az))
        if self.tar_az > 540.0: 
            self.tar_az = 540.0
            self.azTextBox.setText(str(self.tar_az))
        self.az_compass.set_tar_az(self.tar_az)

    def elTextBoxReturnPressed(self):
        self.tar_el = float(self.elTextBox.text())
        self.updateElevation()
        self.callback.set_position(self.tar_az, self.tar_el)
    
    def elPlusPtOneButtonClicked(self):
        self.tar_el = self.tar_el + 0.1
        self.updateElevation()
        self.callback.set_position(self.tar_az, self.tar_el)

    def elPlusOneButtonClicked(self):
        self.tar_el = self.tar_el + 1
        self.updateElevation()
        self.callback.set_position(self.tar_az, self.tar_el)

    def elPlusTenButtonClicked(self):
        self.tar_el = self.tar_el + 10
        self.updateElevation()
        self.callback.set_position(self.tar_az, self.tar_el)

    def elMinusPtOneButtonClicked(self):
        self.tar_el = self.tar_el - 0.1
        self.updateElevation()
        self.callback.set_position(self.tar_az, self.tar_el)

    def elMinusOneButtonClicked(self):
        self.tar_el = self.tar_el - 1
        self.updateElevation()
        self.callback.set_position(self.tar_az, self.tar_el)

    def elMinusTenButtonClicked(self):
        self.tar_el = self.tar_el - 10
        self.updateElevation()
        self.callback.set_position(self.tar_az, self.tar_el)

    def updateElevation(self):
        if self.tar_el < 0: 
            self.tar_el = 0
            self.elTextBox.setText(str(self.tar_el))
        if self.tar_el > 180: 
            self.tar_el = 180
            self.elTextBox.setText(str(self.tar_el))
        self.el_compass.set_tar_el(self.tar_el)

    def initTabControl(self):
        self.tabs = QtGui.QTabWidget()
        self.tabs.setTabPosition(QtGui.QTabWidget.South)

        self.main_tab = QtGui.QWidget()	
        self.main_tab.grid = QtGui.QGridLayout()
        self.tabs.addTab(self.main_tab,"Main")
        self.main_tab.setAutoFillBackground(True)
        p = self.main_tab.palette()
        p.setColor(self.main_tab.backgroundRole(), QtCore.Qt.black)        
        self.main_tab.setPalette(p)

        self.cal_tab = QtGui.QWidget()	
        self.cal_tab.grid = QtGui.QGridLayout()
        self.tabs.addTab(self.cal_tab,"Cal")
        self.cal_tab.setAutoFillBackground(True)
        p = self.cal_tab.palette()
        p.setColor(self.cal_tab.backgroundRole(), QtCore.Qt.black)        
        self.cal_tab.setPalette(p)

        self.config_tab = QtGui.QWidget()	
        self.config_tab_grid = QtGui.QGridLayout()
        self.tabs.addTab(self.config_tab,"Config")
        self.config_tab.setAutoFillBackground(True)
        p = self.config_tab.palette()
        p.setColor(self.config_tab.backgroundRole(), QtCore.Qt.black)        
        self.config_tab.setPalette(p)

        self.main_window.grid.addWidget(self.tabs)

    def initMainTab(self):
        self.initMainTabFrames()
        self.initDials()
        #Init Az Increment Control
        self.initAzControls()
        #Init El Increment Control
        self.initElControls()
        #Init Control Frame
        self.initControlFrame()

        self.main_tab_grid = QtGui.QGridLayout()
        self.main_tab_grid.addWidget(self.control_fr ,0,0,2,2)
        self.main_tab_grid.addWidget(self.az_dial_fr ,0,2,1,3)
        self.main_tab_grid.addWidget(self.az_ctrl_fr ,1,2,1,3)
        self.main_tab_grid.addWidget(self.el_dial_fr ,0,5,1,3)
        self.main_tab_grid.addWidget(self.el_ctrl_fr ,1,5,1,3)
        self.main_tab_grid.setRowStretch(0,1)
        self.main_tab_grid.setColumnStretch(2,1)
        self.main_tab_grid.setColumnStretch(5,1)
        self.main_tab.setLayout(self.main_tab_grid)

    def initMainTabFrames(self):
        self.az_dial_fr = QtGui.QFrame(self)
        self.az_dial_fr.setFrameShape(QtGui.QFrame.StyledPanel)
        self.az_dial_fr_grid = QtGui.QGridLayout()
        self.az_dial_fr.setLayout(self.az_dial_fr_grid)

        self.az_ctrl_fr = QtGui.QFrame()
        self.az_ctrl_fr.setFrameShape(QtGui.QFrame.StyledPanel)

        self.el_dial_fr = QtGui.QFrame(self)
        self.el_dial_fr.setFrameShape(QtGui.QFrame.StyledPanel)
        self.el_dial_fr_grid = QtGui.QGridLayout()
        self.el_dial_fr.setLayout(self.el_dial_fr_grid)

        self.el_ctrl_fr = QtGui.QFrame()
        self.el_ctrl_fr.setFrameShape(QtGui.QFrame.StyledPanel)

        self.control_fr = QtGui.QFrame(self)
        self.control_fr.setFrameShape(QtGui.QFrame.StyledPanel)

    def initDials(self):
        self.el_compass = el_QwtDial(self.el_dial_fr_grid)
        self.az_compass = az_QwtDial(self.az_dial_fr_grid)

    def initAzControls(self):
        self.azMinusTenButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azMinusTenButton.setText("-10.0")
        self.azMinusTenButton.setMinimumWidth(45)

        self.azMinusOneButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azMinusOneButton.setText("-1.0")
        self.azMinusOneButton.setMinimumWidth(45)

        self.azMinusPtOneButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azMinusPtOneButton.setText("-0.1")
        self.azMinusPtOneButton.setMinimumWidth(45)

        self.azPlusPtOneButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azPlusPtOneButton.setText("+0.1")
        self.azPlusPtOneButton.setMinimumWidth(45)

        self.azPlusOneButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azPlusOneButton.setText("+1.0")
        self.azPlusOneButton.setMinimumWidth(45)

        self.azPlusTenButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azPlusTenButton.setText("+10.0")
        self.azPlusTenButton.setMinimumWidth(45)

        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.azMinusTenButton)
        hbox1.addWidget(self.azMinusOneButton)
        hbox1.addWidget(self.azMinusPtOneButton)
        hbox1.addWidget(self.azPlusPtOneButton)
        hbox1.addWidget(self.azPlusOneButton)
        hbox1.addWidget(self.azPlusTenButton)
        self.az_ctrl_fr.setLayout(hbox1)

    def initElControls(self):
        self.elMinusTenButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elMinusTenButton.setText("-10.0")
        self.elMinusTenButton.setMinimumWidth(45)

        self.elMinusOneButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elMinusOneButton.setText("-1.0")
        self.elMinusOneButton.setMinimumWidth(45)

        self.elMinusPtOneButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elMinusPtOneButton.setText("-0.1")
        self.elMinusPtOneButton.setMinimumWidth(45)

        self.elPlusPtOneButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elPlusPtOneButton.setText("+0.1")
        self.elPlusPtOneButton.setMinimumWidth(45)
        
        self.elPlusOneButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elPlusOneButton.setText("+1.0")
        self.elPlusOneButton.setMinimumWidth(45)

        self.elPlusTenButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elPlusTenButton.setText("+10.0")
        self.elPlusTenButton.setMinimumWidth(45)

        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.elMinusTenButton)
        hbox1.addWidget(self.elMinusOneButton)
        hbox1.addWidget(self.elMinusPtOneButton)
        hbox1.addWidget(self.elPlusPtOneButton)
        hbox1.addWidget(self.elPlusOneButton)
        hbox1.addWidget(self.elPlusTenButton)
        self.el_ctrl_fr.setLayout(hbox1)

    def initControlFrame(self):
        self.entry_fr = QtGui.QFrame(self)
        self.entry_fr.setFrameShape(QtGui.QFrame.StyledPanel)

        self.predict_fr = QtGui.QFrame(self)
        self.predict_fr.setFrameShape(QtGui.QFrame.StyledPanel)

        self.dir_fr = QtGui.QFrame(self)
        self.dir_fr.setFrameShape(QtGui.QFrame.StyledPanel)
        #self.dir_fr.setEnabled(False)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.entry_fr)
        vbox.addWidget(self.dir_fr)
        vbox.addWidget(self.predict_fr)
        self.initEntryBoxControls()
        self.initMotorCtrl()
        self.initGpredict()
        self.control_fr.setLayout(vbox)

    def initEntryBoxControls(self):
        self.updateButton = QtGui.QPushButton("Update")
        self.homeButton = QtGui.QPushButton("Home")
        self.queryButton  = QtGui.QPushButton("Query")
        self.connectButton  = QtGui.QPushButton("Connect to Daemon")

        self.azLabel = QtGui.QLabel("Az:")
        self.azLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.azLabel.setStyleSheet("QLabel {color:rgb(0,0,255);}")

        self.azTextBox = QtGui.QLineEdit()
        self.azTextBox.setText("000.0")
        self.azTextBox.setInputMask("#000.0;")
        self.azTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.azTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.azTextBox.setMaxLength(5)
        self.azTextBox.setFixedWidth(60)
        self.azTextBox.setFixedHeight(20)

        self.elLabel = QtGui.QLabel("El:")
        self.elLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.elLabel.setStyleSheet("QLabel {color:rgb(0,0,255);}")

        self.elTextBox = QtGui.QLineEdit(self.el_dial_fr)
        self.elTextBox.setText("000.0")
        self.elTextBox.setInputMask("000.0;")
        self.elTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.elTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.elTextBox.setMaxLength(5)
        self.elTextBox.setFixedWidth(60)
        self.elTextBox.setFixedHeight(20)

        self.ssidLabel = QtGui.QLabel("Subsystem:")
        self.ssidLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.ssidLabel.setStyleSheet("QLabel {color:rgb(255,255,255);}")

        self.ssidCombo = QtGui.QComboBox(self)
        self.ssidCombo.addItem("VHF/UHF")
        self.ssidCombo.addItem("3.0m Dish")
        self.ssidCombo.addItem("4.5m Dish")
        self.ssidCombo.addItem("NOAA WX")

        self.fb_query_rate_le = QtGui.QLineEdit()
        self.fb_query_rate_le.setText("0.25")
        self.query_val = QtGui.QDoubleValidator()
        self.fb_query_rate_le.setValidator(self.query_val)
        self.fb_query_rate_le.setEchoMode(QtGui.QLineEdit.Normal)
        self.fb_query_rate_le.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.fb_query_rate_le.setMaxLength(4)
        self.fb_query_rate_le.setFixedWidth(50)

        self.autoQuery_cb = QtGui.QCheckBox("Auto Query [s]")  
        self.autoQuery_cb.setStyleSheet("QCheckBox { background-color:rgb(0,0,0); color:rgb(255,0,0); }")
        self.autoQuery_cb.setChecked(True)

        az_hbox = QtGui.QHBoxLayout()
        az_hbox.addWidget(self.azLabel)
        az_hbox.addWidget(self.azTextBox)

        el_hbox = QtGui.QHBoxLayout()
        el_hbox.addWidget(self.elLabel)
        el_hbox.addWidget(self.elTextBox)

        btn_hbox = QtGui.QHBoxLayout()
        btn_hbox.addWidget(self.homeButton)
        btn_hbox.addWidget(self.updateButton)
        
        ssid_hbox = QtGui.QHBoxLayout()
        ssid_hbox.addWidget(self.queryButton)
        ssid_hbox.addWidget(self.ssidCombo)

        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.autoQuery_cb)
        hbox1.addWidget(self.fb_query_rate_le)

        hbox2 = QtGui.QHBoxLayout()
        hbox2.addLayout(az_hbox)
        hbox2.addLayout(el_hbox)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox2)
        vbox.addLayout(btn_hbox)
        vbox.addLayout(ssid_hbox)
        vbox.addLayout(hbox1)
        vbox.addWidget(self.connectButton)
        
        self.entry_fr.setLayout(vbox)

        

    def initMotorCtrl(self):
        self.motor_lbl = QtGui.QLabel("     Direct Motor Drive     ")
        self.motor_lbl.setAlignment(QtCore.Qt.AlignCenter|QtCore.Qt.AlignVCenter)
        self.motor_lbl.setFixedHeight(20)
        self.motor_lbl.setStyleSheet("QLabel {color:rgb(255,255,255);}")

        self.UpLeftButton = QtGui.QPushButton("U+L")
        self.UpLeftButton.setFixedWidth(50)
        self.UpLeftButton.setFixedHeight(20)

        self.UpButton = QtGui.QPushButton("Up")
        self.UpButton.setFixedWidth(50)
        self.UpButton.setFixedHeight(20)

        self.UpRightButton = QtGui.QPushButton("U+R")
        self.UpRightButton.setFixedWidth(50)
        self.UpRightButton.setFixedHeight(20)

        self.LeftButton = QtGui.QPushButton("Left")
        self.LeftButton.setFixedWidth(50)
        self.LeftButton.setFixedHeight(20)

        self.StopButton = QtGui.QPushButton("STOP!")
        self.StopButton.setFixedWidth(50)
        self.StopButton.setFixedHeight(20)

        self.RightButton = QtGui.QPushButton("Right")
        self.RightButton.setFixedWidth(50)
        self.RightButton.setFixedHeight(20)

        self.DnLeftButton = QtGui.QPushButton("D+L")
        self.DnLeftButton.setFixedWidth(50)
        self.DnLeftButton.setFixedHeight(20)

        self.DownButton = QtGui.QPushButton("Down")
        self.DownButton.setFixedWidth(50)
        self.DownButton.setFixedHeight(20)

        self.DnRightButton = QtGui.QPushButton("D+R")
        self.DnRightButton.setFixedWidth(50)
        self.DnRightButton.setFixedHeight(20)

        vbox = QtGui.QVBoxLayout()
        hbox1 = QtGui.QHBoxLayout()
        hbox2 = QtGui.QHBoxLayout()
        hbox3 = QtGui.QHBoxLayout()

        hbox1.setContentsMargins(0,0,0,0)
        hbox1.addWidget(self.UpLeftButton)
        hbox1.addWidget(self.UpButton)
        hbox1.addWidget(self.UpRightButton)

        hbox2.setContentsMargins(0,0,0,0)
        hbox2.addWidget(self.LeftButton)
        hbox2.addWidget(self.StopButton)
        hbox2.addWidget(self.RightButton)

        hbox3.setContentsMargins(0,0,0,0)
        hbox3.addWidget(self.DnLeftButton)
        hbox3.addWidget(self.DownButton)
        hbox3.addWidget(self.DnRightButton)

        vbox.setContentsMargins(0,0,0,0)
        vbox.addWidget(self.motor_lbl)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        self.dir_fr.setLayout(vbox)

    def initGpredict(self):
        self.ipAddrTextBox = QtGui.QLineEdit()
        self.ipAddrTextBox.setText('127.000.000.001')
        self.ipAddrTextBox.setInputMask("000.000.000.000;")
        self.ipAddrTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.ipAddrTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.ipAddrTextBox.setMaxLength(15)

        self.portTextBox = QtGui.QLineEdit()
        self.portTextBox.setText('4533')
        self.port_validator = QtGui.QIntValidator()
        self.port_validator.setRange(0,65535)
        self.portTextBox.setValidator(self.port_validator)
        self.portTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.portTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.portTextBox.setMaxLength(5)
        self.portTextBox.setFixedWidth(50)

        label = QtGui.QLabel('Status:')
        label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        label.setStyleSheet("QLabel {color:rgb(255,255,255);}")
        label.setFixedHeight(10)
        self.pred_status_lbl = QtGui.QLabel('Disconnected')
        self.pred_status_lbl.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.pred_status_lbl.setStyleSheet("QLabel {font-weight:bold; color:rgb(255,0,0);}")
        self.pred_status_lbl.setFixedWidth(125)
        self.pred_status_lbl.setFixedHeight(10)

        self.predictButton = QtGui.QPushButton("Start Server")

        lbl1 = QtGui.QLabel('Az:')
        lbl1.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        lbl1.setStyleSheet("QLabel {color:rgb(255,255,255)}")
        lbl1.setFixedWidth(25)
        lbl1.setFixedHeight(10)
    
        lbl2 = QtGui.QLabel('El:')
        lbl2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        lbl2.setStyleSheet("QLabel {color:rgb(255,255,255)}")
        lbl2.setFixedWidth(25)
        lbl2.setFixedHeight(10)

        self.pred_az_lbl = QtGui.QLabel('XXX.X')
        self.pred_az_lbl.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.pred_az_lbl.setStyleSheet("QLabel {color:rgb(255,255,255)}")
        self.pred_az_lbl.setFixedWidth(50)
        self.pred_az_lbl.setFixedHeight(10)

        self.pred_el_lbl = QtGui.QLabel('XXX.X')
        self.pred_el_lbl.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.pred_el_lbl.setStyleSheet("QLabel {color:rgb(255,255,255)}")
        self.pred_el_lbl.setFixedWidth(50)
        self.pred_el_lbl.setFixedHeight(10)

        self.autoTrack_cb = QtGui.QCheckBox("Auto Track")  
        self.autoTrack_cb.setStyleSheet("QCheckBox { background-color:rgb(0,0,0); color:rgb(255,255,255); }")
        self.autoTrack_cb.setFixedHeight(20)

        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.ipAddrTextBox)
        hbox1.addWidget(self.portTextBox)

        hbox2 = QtGui.QHBoxLayout()
        hbox2.addWidget(label)
        hbox2.addWidget(self.pred_status_lbl)

        hbox3 = QtGui.QHBoxLayout()
        hbox3.addWidget(lbl1)
        hbox3.addWidget(self.pred_az_lbl)

        hbox4 = QtGui.QHBoxLayout()
        hbox4.addWidget(lbl2)
        hbox4.addWidget(self.pred_el_lbl)

        vbox1 = QtGui.QVBoxLayout()
        vbox1.addLayout(hbox3)
        vbox1.addLayout(hbox4)

        hbox5 = QtGui.QHBoxLayout()
        hbox5.addWidget(self.autoTrack_cb)
        hbox5.addLayout(vbox1)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addWidget(self.predictButton)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox5)

        self.predict_fr.setLayout(vbox)

    def initCalTab(self):
        #Init Set Angles
        self.initCalAnglesControls()
        #Init Motor Power Control
        self.initMotorPower()   
        
        self.cal_tab_grid = QtGui.QGridLayout()
        self.cal_tab_grid.addWidget(self.cal_angle_fr,0,0,1,1)
        self.cal_tab_grid.addWidget(self.mot_power_fr,0,1,1,1)
        self.cal_tab_grid.setColumnStretch(2,1)
        self.cal_tab_grid.setRowStretch(2,1)
        self.cal_tab.setLayout(self.cal_tab_grid)

    def initMotorPower(self):
        self.mot_power_fr = QtGui.QFrame(self)
        self.mot_power_fr.setFrameShape(QtGui.QFrame.StyledPanel)

        fr_lbl = QtGui.QLabel("      Motor Power      ")
        fr_lbl.setAlignment(QtCore.Qt.AlignCenter|QtCore.Qt.AlignVCenter)
        fr_lbl.setStyleSheet("QLabel {text-decoration:underline; color:rgb(255,255,255);}")

        self.setMotPowerButton = QtGui.QPushButton("Set")
        
        self.azPowLabel = QtGui.QLabel("Azimuth:")
        self.azPowLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.azPowLabel.setStyleSheet("QLabel {color:rgb(255,255,255);}")

        self.azPowTextBox = QtGui.QLineEdit()
        self.azPowTextBox.setText("64")
        self.azPowTextBox.setInputMask("00;")
        self.azPowTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.azPowTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.azPowTextBox.setMaxLength(2)
        self.azPowTextBox.setFixedWidth(60)

        self.elPowLabel = QtGui.QLabel("Elevation:")
        self.elPowLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.elPowLabel.setStyleSheet("QLabel {color:rgb(255,255,255);}")

        self.elPowTextBox = QtGui.QLineEdit(self.el_dial_fr)
        self.elPowTextBox.setText("64")
        self.elPowTextBox.setInputMask("00;")
        self.elPowTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.elPowTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.elPowTextBox.setMaxLength(2)
        self.elPowTextBox.setFixedWidth(60)

        az_hbox = QtGui.QHBoxLayout()
        az_hbox.addWidget(self.azPowLabel)
        az_hbox.addWidget(self.azPowTextBox)

        el_hbox = QtGui.QHBoxLayout()
        el_hbox.addWidget(self.elPowLabel)
        el_hbox.addWidget(self.elPowTextBox)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(fr_lbl)
        vbox.addLayout(az_hbox)
        vbox.addLayout(el_hbox)
        vbox.addWidget(self.setMotPowerButton)
        self.mot_power_fr.setLayout(vbox)

    def initCalAnglesControls(self):
        self.cal_angle_fr = QtGui.QFrame(self)
        self.cal_angle_fr.setFrameShape(QtGui.QFrame.StyledPanel)

        self.setCalButton = QtGui.QPushButton("Set")
        self.setCalButton.setFixedWidth(60)
        self.zeroButton = QtGui.QPushButton("Zero")
        self.zeroButton.setFixedWidth(60)

        fr_lbl = QtGui.QLabel("    Calibrate Angles    ")
        fr_lbl.setAlignment(QtCore.Qt.AlignCenter|QtCore.Qt.AlignVCenter)
        fr_lbl.setStyleSheet("QLabel {text-decoration:underline; color:rgb(255,255,255);}")

        self.azCalLabel = QtGui.QLabel("Azimuth:")
        self.azCalLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.azCalLabel.setStyleSheet("QLabel {color:rgb(255,0,0);}")

        self.azCalTextBox = QtGui.QLineEdit()
        self.azCalTextBox.setText("000.0")
        self.azCalTextBox.setInputMask("#000.0;")
        self.azCalTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.azCalTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.azCalTextBox.setMaxLength(6)
        self.azCalTextBox.setFixedWidth(60)

        self.elCalLabel = QtGui.QLabel("Elevation:")
        self.elCalLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.elCalLabel.setStyleSheet("QLabel {color:rgb(255,0,0);}")

        self.elCalTextBox = QtGui.QLineEdit(self.el_dial_fr)
        self.elCalTextBox.setText("000.0")
        self.elCalTextBox.setInputMask("000.0;")
        self.elCalTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.elCalTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.elCalTextBox.setMaxLength(6)
        self.elCalTextBox.setFixedWidth(60)

        az_hbox = QtGui.QHBoxLayout()
        az_hbox.addWidget(self.azCalLabel)
        az_hbox.addWidget(self.azCalTextBox)

        el_hbox = QtGui.QHBoxLayout()
        el_hbox.addWidget(self.elCalLabel)
        el_hbox.addWidget(self.elCalTextBox)

        btn_hbox= QtGui.QHBoxLayout()
        btn_hbox.addWidget(self.zeroButton)
        btn_hbox.addWidget(self.setCalButton)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(fr_lbl)
        vbox.addLayout(az_hbox)
        vbox.addLayout(el_hbox)
        vbox.addLayout(btn_hbox)

        self.cal_angle_fr.setLayout(vbox)
    def darken(self):
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background,QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.WindowText,QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.Text,QtCore.Qt.white)
        self.setPalette(palette)

    def utc_ts(self):
        return str(date.utcnow()) + " UTC | "

