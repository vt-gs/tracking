#!/usr/bin/env python

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import Qt

import PyQt4.Qwt5 as Qwt
import numpy as np
from datetime import datetime as date
import sys
#from az_dial import *
from az_QwtDial import *
from el_QwtDial import *
import time
from gpredict import *
from control_button_frame import *
from lcd_feedback_frame import *

class main_widget(QtGui.QWidget):
    def __init__(self):
        super(main_widget, self).__init__()
        self.initUI()
       
    def initUI(self):
        self.grid = QtGui.QGridLayout()
        #self.setLayout(self.grid)

class MainWindow(QtGui.QMainWindow):
    def __init__(self, options):
        #QtGui.QMainWindow.__init__(self)
        super(MainWindow, self).__init__()
        self.resize(850, 425)
        self.setMinimumWidth(800)
        #self.setMaximumWidth(900)
        self.setMinimumHeight(425)
        #self.setMaximumHeight(700)
        self.setWindowTitle('VTGS Tracking GUI v2.0')
        #self.setContentsMargins(0,0,0,0)
        self.main_window = main_widget()
        self.setCentralWidget(self.main_window)

        self.ip   = options.ip
        self.port = options.port
        self.ssid = options.ssid
        self.uid  = options.uid

        #self.statusBar().showMessage("| Disconnected | Manual | Current Az: 000.0 | Current El: 000.0 |")
        self.init_variables()
        self.init_ui()
        self.darken()
        #self.setFocus()

    def init_variables(self):
        self.connected = False #TCP/IP Connection to Daemon
        self.daemon_state = 'IDLE'

        self.cur_az = 0
        self.cur_az_rate = 0
        self.tar_az = 0
        self.cur_el = 0
        self.cur_el_rate = 0
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

    def init_ui(self):
        self.init_frames()
        self.init_ctrl_frame()  
        self.init_connect_frame() 
        self.init_predict_frame()   
        #self.initTimers()
        self.connect_signals()
        self.show()

    def connect_signals(self):

        self.connect_button.clicked.connect(self.connect_button_event)
        self.session_button.clicked.connect(self.session_button_event)

        self.query_button.clicked.connect(self.query_button_event) 
        self.stop_button.clicked.connect(self.stop_button_event) 
        self.home_button.clicked.connect(self.home_button_event)
        self.update_button.clicked.connect(self.update_button_event)  
        self.auto_query_cb.stateChanged.connect(self.auto_query_cb_event)

        self.ssid_combo.activated[int].connect(self.update_ssid_event)

    def increment_target_angle(self, az_el, val):
        #Called by button control frame
        if az_el == 'az':
            self.tar_az += val
            self.update_target_azimuth()
        elif az_el == 'el':
            self.tar_el += val
            self.update_target_elevation()

    def update_target_azimuth(self):
        if self.tar_az < -180.0: 
            self.tar_az = -180.0
            self.azTextBox.setText(str(self.tar_az))
        if self.tar_az > 540.0: 
            self.tar_az = 540.0
            self.azTextBox.setText(str(self.tar_az))
        self.az_compass.set_tar_az(self.tar_az)
        self.az_lcd_fr.set_tar(self.tar_az)

    def update_target_elevation(self):
        if self.tar_el < 0: 
            self.tar_el = 0
            self.elTextBox.setText(str(self.tar_el))
        if self.tar_el > 180: 
            self.tar_el = 180
            self.elTextBox.setText(str(self.tar_el))
        self.el_compass.set_tar_el(self.tar_el)
        self.el_lcd_fr.set_tar(self.tar_el)

    def update_ssid_event(self, idx):
        if   idx == 0: #VUL
            self.ssid = 'VUL'
            self.port = 2000
        elif idx == 1: #3M0
            self.ssid = '3M0'
            self.port = 2001
        elif idx == 2: #4M5
            self.ssid = '4M5'
            self.port = 2002
        elif idx == 3: #WX
            self.ssid = 'WX'
            self.port = 2003
        print self.utc_ts() + "Updated Subsystem ID: " + self.ssid
        print self.utc_ts() + "Updated Daemon port number: " + str(self.port)
        self.callback.set_ssid(self.ssid)

    def connect_button_event(self):
        if self.connected == False:
            print self.utc_ts() + "Connecting to Daemon..."
            self.connected = self.callback.connect(self.ip, self.port,self)
        elif self.connected == True:
            print self.utc_ts() + "Disconnecting from Daemon..."
            self.connected = self.callback.disconnect()
            self.set_daemon_state('IDLE')

        if self.connected == True:
            self.connect_button.setText('Disconnect')
            self.conn_status_lbl.setText('CONNECTED')
            self.conn_status_lbl.setStyleSheet("QLabel {font-weight:bold; color:rgb(0,255,0);}")
            self.uid = str(self.uid_tb.text())
            print self.utc_ts() + 'Locking Down USERID for SESSION: ' + str(self.uid)
            print self.utc_ts() + '  Locking Down SSID for SESSION: ' + str(self.ssid)
            self.ssid_combo.setEnabled(False)
            self.uid_tb.setEnabled(False)
            self.session_button.setEnabled(True)
        elif self.connected == False:
            self.connect_button.setText('Connect')
            self.conn_status_lbl.setText('DISCONNECTED')
            self.conn_status_lbl.setStyleSheet("QLabel {font-weight:bold; color:rgb(255,0,0);}")
            self.ssid_combo.setEnabled(True)
            self.uid_tb.setEnabled(True)
            self.session_button.setEnabled(False)

    def session_button_event(self):
        #USer is attempting to start a tracking session
        #is the daemon in a STANDBY State?
        if self.daemon_state == 'STANDBY':
            print self.utc_ts() + "Requesting Session START"
            self.callback.set_session_start(self)
            #self.session_button.setText('Stop')
        elif self.daemon_state == 'ACTIVE':
            print self.utc_ts() + "Requesting Session STOP"
            self.callback.set_session_stop(self)
            #self.session_button.setText('Start')

            #daemon is in ACTIVE mode, send stop message

    def query_button_event(self):
        print self.utc_ts() + "Sending MANAGEMENT QUERY"
        self.callback.get_daemon_state(self)
        #need to change above to expect returned value
        #valid = self.callback.get_daemon_state(self)
        #if valid == True:
            
        if self.daemon_state == 'ACTIVE':
            print self.utc_ts() + "Sending MOTION QUERY"
            valid, az, el, az_rate, el_rate = self.callback.get_motion_feedback()

            if valid != -1:
                self.cur_az = az
                self.cur_el = el
                self.cur_az_rate = az_rate
                self.cur_el_rate = el_rate
                self.update_current_angles()
            else:
                self.autoQuery_cb.setCheckState(QtCore.Qt.Unchecked)
     
    def update_current_angles(self):
        self.az_compass.set_cur_az(self.cur_az)
        self.az_lcd_fr.set_cur(self.cur_az)
        self.az_lcd_fr.set_rate(self.cur_az_rate)
        

        self.el_compass.set_cur_el(self.cur_el)
        self.el_lcd_fr.set_cur(self.cur_el)
        self.el_lcd_fr.set_rate(self.cur_el_rate)

    def stop_button_event(self):
        pass

    def home_button_event(self):
        pass

    def update_button_event(self):
        pass

    def auto_query_cb_event(self, state):
        CheckState = (state == QtCore.Qt.Checked)
        if CheckState == True:  
            #self.updateTimer.start()
            print self.utc_ts() + "Started Auto Update, Interval: " + str(self.update_rate) + " [ms]"
        else:
            #self.updateTimer.stop()
            print self.utc_ts() + "Stopped Auto Update"

    def set_daemon_state(self, state):
        self.daemon_state = state
        self.daemon_state_lbl.setText(state)
        if self.daemon_state == 'IDLE':
            self.daemon_state_lbl.setStyleSheet("QLabel {font-weight:bold; color:rgb(255,255,255);}")
            self.session_button.setText('Start')
            self.ctrl_fr.setEnabled(False)
        elif self.daemon_state == 'STANDBY':
            self.daemon_state_lbl.setStyleSheet("QLabel {font-weight:bold; color:rgb(255,255,0);}")
            self.session_button.setText('Start')
            self.ctrl_fr.setEnabled(False)
        elif self.daemon_state == 'ACTIVE':
            self.daemon_state_lbl.setStyleSheet("QLabel {font-weight:bold; color:rgb(0,255,0);}")
            self.session_button.setText('Stop')
            self.ctrl_fr.setEnabled(True)

    def init_connect_frame(self):
        uid_lbl = QtGui.QLabel("User ID:")
        uid_lbl.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        uid_lbl.setStyleSheet("QLabel {color:rgb(255,255,255);}")
        uid_lbl.setFixedHeight(10)
        uid_lbl.setFixedWidth(60)
        self.uid_tb = QtGui.QLineEdit()
        self.uid_tb.setText(self.uid)
        self.uid_tb.setEchoMode(QtGui.QLineEdit.Normal)
        self.uid_tb.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.uid_tb.setMaxLength(15)
        self.uid_tb.setFixedHeight(20)

        uid_hbox = QtGui.QHBoxLayout()
        uid_hbox.addWidget(uid_lbl)
        uid_hbox.addWidget(self.uid_tb)

        self.connect_button  = QtGui.QPushButton("Connect")
        self.session_button  = QtGui.QPushButton("Start")
        self.session_button.setEnabled(False)

        btn_hbox = QtGui.QHBoxLayout()
        btn_hbox.addWidget(self.connect_button)
        btn_hbox.addWidget(self.session_button)

        self.ssidLabel = QtGui.QLabel("SSID:")
        self.ssidLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.ssidLabel.setStyleSheet("QLabel {color:rgb(255,255,255);}")
        self.ssidLabel.setFixedWidth(60)
        self.ssid_combo = QtGui.QComboBox(self)
        self.ssid_combo.addItem("VHF/UHF")
        self.ssid_combo.addItem("3.0m Dish")
        self.ssid_combo.addItem("4.5m Dish")
        self.ssid_combo.addItem("NOAA WX")
        self.ssid_combo.setFixedHeight(25)
        if self.ssid =='VUL': self.ssid_combo.setCurrentIndex(0)
        if self.ssid =='3M0': self.ssid_combo.setCurrentIndex(1)
        if self.ssid =='4M5': self.ssid_combo.setCurrentIndex(2)
        if self.ssid =='WX': self.ssid_combo.setCurrentIndex(3)

        status_lbl = QtGui.QLabel('Status:')
        status_lbl.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        status_lbl.setStyleSheet("QLabel {color:rgb(255,255,255);}")
        status_lbl.setFixedHeight(10)
        status_lbl.setFixedWidth(60)
        self.conn_status_lbl = QtGui.QLabel('Disconnected')
        self.conn_status_lbl.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.conn_status_lbl.setStyleSheet("QLabel {font-weight:bold; color:rgb(255,0,0);}")
        self.conn_status_lbl.setFixedWidth(125)
        self.conn_status_lbl.setFixedHeight(10)
        
        state_lbl = QtGui.QLabel('State:')
        state_lbl.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        state_lbl.setStyleSheet("QLabel {color:rgb(255,255,255);}")
        state_lbl.setFixedHeight(10)
        state_lbl.setFixedWidth(60)
        self.daemon_state_lbl = QtGui.QLabel('IDLE')
        self.daemon_state_lbl.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.daemon_state_lbl.setStyleSheet("QLabel {font-weight:bold; color:rgb(255,255,255);}")
        self.daemon_state_lbl.setFixedWidth(125)
        self.daemon_state_lbl.setFixedHeight(10)

        ssid_hbox = QtGui.QHBoxLayout()
        ssid_hbox.addWidget(self.ssidLabel)
        ssid_hbox.addWidget(self.ssid_combo)

        hbox2 = QtGui.QHBoxLayout()
        hbox2.addWidget(status_lbl)
        hbox2.addWidget(self.conn_status_lbl)

        hbox3 = QtGui.QHBoxLayout()
        hbox3.addWidget(state_lbl)
        hbox3.addWidget(self.daemon_state_lbl)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(uid_hbox)
        vbox.addLayout(ssid_hbox)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        vbox.addLayout(btn_hbox)
        vbox.addStretch(1)
        self.con_fr.setLayout(vbox)

    def init_ctrl_frame(self):
        self.update_button = QtGui.QPushButton("Update")
        self.home_button = QtGui.QPushButton("Home")
        self.query_button = QtGui.QPushButton("Query")
        self.stop_button = QtGui.QPushButton("Stop")

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

        self.elTextBox = QtGui.QLineEdit()
        self.elTextBox.setText("000.0")
        self.elTextBox.setInputMask("000.0;")
        self.elTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.elTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.elTextBox.setMaxLength(5)
        self.elTextBox.setFixedWidth(60)
        self.elTextBox.setFixedHeight(20)

        self.fb_query_rate_le = QtGui.QLineEdit()
        self.fb_query_rate_le.setText("0.25")
        self.query_val = QtGui.QDoubleValidator()
        self.fb_query_rate_le.setValidator(self.query_val)
        self.fb_query_rate_le.setEchoMode(QtGui.QLineEdit.Normal)
        self.fb_query_rate_le.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.fb_query_rate_le.setMaxLength(4)
        self.fb_query_rate_le.setFixedWidth(50)
        self.fb_query_rate_le.setFixedHeight(20)

        self.auto_query_cb = QtGui.QCheckBox("Auto Query [s]")  
        self.auto_query_cb.setStyleSheet("QCheckBox { background-color:rgb(0,0,0); color:rgb(255,0,0); }")
        self.auto_query_cb.setChecked(True)

        az_hbox = QtGui.QHBoxLayout()
        az_hbox.addWidget(self.azLabel)
        az_hbox.addWidget(self.azTextBox)

        el_hbox = QtGui.QHBoxLayout()
        el_hbox.addWidget(self.elLabel)
        el_hbox.addWidget(self.elTextBox)

        btn_hbox1 = QtGui.QHBoxLayout()
        btn_hbox1.addWidget(self.stop_button)
        btn_hbox1.addWidget(self.update_button)

        btn_hbox2 = QtGui.QHBoxLayout()
        btn_hbox2.addWidget(self.query_button)
        btn_hbox2.addWidget(self.home_button)
        
        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.auto_query_cb)
        hbox1.addWidget(self.fb_query_rate_le)

        hbox2 = QtGui.QHBoxLayout()
        hbox2.addLayout(az_hbox)
        hbox2.addLayout(el_hbox)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox2)
        vbox.addLayout(btn_hbox1)
        vbox.addLayout(btn_hbox2)
        vbox.addLayout(hbox1)
        
        self.ctrl_fr.setLayout(vbox)

    def init_predict_frame(self):
        self.ipAddrTextBox = QtGui.QLineEdit()
        self.ipAddrTextBox.setText('127.000.000.001')
        self.ipAddrTextBox.setInputMask("000.000.000.000;")
        self.ipAddrTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.ipAddrTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.ipAddrTextBox.setMaxLength(15)
        self.ipAddrTextBox.setFixedHeight(20)

        self.portTextBox = QtGui.QLineEdit()
        self.portTextBox.setText('4533')
        self.port_validator = QtGui.QIntValidator()
        self.port_validator.setRange(0,65535)
        self.portTextBox.setValidator(self.port_validator)
        self.portTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.portTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.portTextBox.setMaxLength(5)
        self.portTextBox.setFixedWidth(50)
        self.portTextBox.setFixedHeight(20)

        label = QtGui.QLabel('Status:')
        label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        label.setStyleSheet("QLabel {color:rgb(255,255,255);}")
        label.setFixedHeight(10)
        self.pred_status_lbl = QtGui.QLabel('Disconnected')
        self.pred_status_lbl.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.pred_status_lbl.setStyleSheet("QLabel {font-weight:bold; color:rgb(255,0,0);}")
        self.pred_status_lbl.setFixedWidth(125)
        self.pred_status_lbl.setFixedHeight(10)

        self.predictButton = QtGui.QPushButton("Start Predict Server")
        self.predictButton.setFixedHeight(20)

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

        self.pred_fr.setLayout(vbox)

    def init_frames(self):
        self.ctrl_fr = QtGui.QFrame(self)
        self.ctrl_fr.setFrameShape(QtGui.QFrame.StyledPanel)
        self.ctrl_fr.setEnabled(False)
        self.con_fr = QtGui.QFrame(self)
        self.con_fr.setFrameShape(QtGui.QFrame.StyledPanel)
        self.pred_fr = QtGui.QFrame(self)
        self.pred_fr.setFrameShape(QtGui.QFrame.StyledPanel)
        
        self.az_fr = QtGui.QFrame(self)
        self.az_fr.setFrameShape(QtGui.QFrame.StyledPanel)
        self.az_compass = az_QwtDial(self.az_fr)

        self.az_lcd_fr = lcd_feedback_frame(self)
        self.az_lcd_fr.setFrameShape(QtGui.QFrame.StyledPanel)

        self.az_ctrl_fr = control_button_frame(self, 'az')
        self.az_ctrl_fr.setFrameShape(QtGui.QFrame.StyledPanel)
        
        self.el_fr = QtGui.QFrame(self)
        self.el_fr.setFrameShape(QtGui.QFrame.StyledPanel)
        self.el_compass = el_QwtDial(self.el_fr)

        self.el_lcd_fr = lcd_feedback_frame(self)
        self.el_lcd_fr.setFrameShape(QtGui.QFrame.StyledPanel)

        self.el_ctrl_fr = control_button_frame(self, 'el')
        self.el_ctrl_fr.setFrameShape(QtGui.QFrame.StyledPanel)

        vbox1 = QtGui.QVBoxLayout()
        vbox1.addWidget(self.con_fr)
        vbox1.addStretch(1)
        vbox1.addWidget(self.ctrl_fr)
        vbox1.addStretch(1) 
        vbox1.addWidget(self.pred_fr)

        self.main_grid = QtGui.QGridLayout()
        self.main_grid.addLayout(vbox1,0,0,4,2)
        self.main_grid.addWidget(self.az_fr     ,0,2,1,3)
        self.main_grid.addWidget(self.az_lcd_fr ,1,2,1,3)
        self.main_grid.addWidget(self.az_ctrl_fr,2,2,1,3)
        self.main_grid.addWidget(self.el_fr     ,0,5,1,3)
        self.main_grid.addWidget(self.el_lcd_fr ,1,5,1,3)
        self.main_grid.addWidget(self.el_ctrl_fr,2,5,1,3)
        self.main_grid.setRowStretch(0,1)
        self.main_grid.setColumnStretch(2,1)
        self.main_grid.setColumnStretch(5,1)
        self.main_window.setLayout(self.main_grid)

    def set_callback(self, callback):
        self.callback = callback

    def darken(self):
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background,QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.WindowText,QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.Text,QtCore.Qt.white)
        self.setPalette(palette)

    def utc_ts(self):
        return str(date.utcnow()) + " UTC | GUI | "


    
