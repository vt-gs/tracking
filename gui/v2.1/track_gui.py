#!/usr/bin/env python
#version 2.1

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
        self.setWindowTitle('VTGS Tracking GUI v2.1')
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
        self.connected = False      #TCP/IP Connection to Daemon
        self.daemon_state = 'IDLE'

        self.cur_az = 0
        self.cur_az_rate = 0
        self.tar_az = 0
        self.cur_el = 0
        self.cur_el_rate = 0
        self.tar_el = 0
        
        if self.ssid == 'VUL':
            self.home_az = 180.0
            self.home_el = 0.0
            self.tar_az = 180.0
            self.tar_el = 0.0
        if self.ssid == '3M0':
            self.home_az = 180.0
            self.home_el = 90.0
            self.tar_az = 180.0
            self.tar_el = 90.0

        self.callback    = None   #Callback accessor for tracking control
        self.update_rate = 250    #Feedback Query Auto Update Interval in milliseconds

        self.pred_az = 0.0
        self.pred_el = 0.0
        self.pred_ip = '127.000.000.001'
        self.pred_port = int(4533)
        self.gpredict  = None     #Callback accessor for gpredict thread control
        self.pred_conn_state = 0   #Gpredict Connection Status, 0=Disconnected, 1=Listening, 2=Connected
        self.autoTrack = False    #auto track mode, True = Auto, False = Manual

    def init_ui(self):
        self.init_frames()
        self.init_ctrl_frame()  
        self.init_connect_frame() 
        self.init_predict_frame()
        
        #initialize target displays
        self.update_target_azimuth()
        self.update_target_elevation()
        self.azTextBox.setText(str(self.tar_az))
        self.elTextBox.setText(str(self.tar_el))

        self.init_timers()
        self.connect_signals()
        self.show()

    def init_timers(self):
        self.update_timer = QtCore.QTimer(self)
        self.update_timer.setInterval(self.update_rate)
        #self.update_timer.start(self.update_rate)

        #Timer used to Poll the GPredict Server thread for updates
        self.predict_timer = QtCore.QTimer(self)
        self.predict_timer.setInterval(self.update_rate)

    def connect_signals(self):
        #Connection Control Signals
        #QtCore.QObject.connect(self.fb_query_rate_le, QtCore.SIGNAL('editingFinished()'), self.updateRate)
        self.ssid_combo.activated[int].connect(self.update_ssid_event)
        self.connect_button.clicked.connect(self.connect_button_event)
        self.session_button.clicked.connect(self.session_button_event)

        #Antenna Control Signals
        self.query_button.clicked.connect(self.query_button_event) 
        self.stop_button.clicked.connect(self.stop_button_event) 
        self.home_button.clicked.connect(self.home_button_event)
        self.update_button.clicked.connect(self.update_button_event)  
        self.auto_query_cb.stateChanged.connect(self.auto_query_cb_event)
        QtCore.QObject.connect(self.fb_query_rate_le, QtCore.SIGNAL('editingFinished()'), self.update_feedback_rate)
        QtCore.QObject.connect(self.update_timer, QtCore.SIGNAL('timeout()'), self.auto_query_timeout)


        #Gpredict Signals
        self.predict_button.clicked.connect(self.predict_button_event)
        QtCore.QObject.connect(self.gpredict_ip_le, QtCore.SIGNAL('editingFinished()'), self.update_predict_ip)
        QtCore.QObject.connect(self.gpredict_port_le, QtCore.SIGNAL('editingFinished()'), self.update_predict_port)
        QtCore.QObject.connect(self.predict_timer, QtCore.SIGNAL('timeout()'), self.update_predict_status)

   

    
    ##### GPREDICT and AUTO TRACK FUNCTIONS #####
    # Functions that deal with Grpedict and auto tracking
    def predict_button_event(self):
        if self.pred_conn_state == 0:  #Disconnected, Start Connection Thread
            self.gpredict = Gpredict_Thread(self, self.pred_ip, self.pred_port,1)
            self.gpredict.daemon = True
            self.gpredict.start()
            #self.pred_conn_state = 1 #listening
            #self.update_predict_status()
            self.predict_timer.start()
        elif ((self.pred_conn_state == 1) or (self.pred_conn_state == 2)):
            self.gpredict.stop()
            self.gpredict.join()
            self.predict_timer.stop()
            self.set_predict_conn_state(0)
            self.update_predict_status()

    def update_predict_ip(self):
        self.pred_ip=self.gpredict_ip_le.text()
    
    def update_predict_port(self):
        self.pred_port = int(self.gpredict_port_le.text())

    def set_predict_conn_state(self, state):
        #function called by gpredict thread    
        self.pred_conn_state = state
        #self.update_predict_status()

    def predict_callback_set(self, az, el):
        #function called by gpredict thread
        #sets target angles when auto tracking
        self.pred_az = az
        self.pred_el = el
        self.pred_az_lbl.setText(str(round(self.pred_az,1)))
        self.pred_el_lbl.setText(str(round(self.pred_el,1)))
        if self.pred_conn_state == 2: #active connection
            if self.auto_track_cb.isChecked() == True: #auto track enables
                self.tar_az = round(self.pred_az, 1)
                self.tar_el = round(self.pred_el,1)
                self.update_target_azimuth()
                self.update_target_elevation()
                self.callback.set_position(self.tar_az, self.tar_el, True)

    def predict_callback_get(self):
        #function called by gpredict thread
        #gets current angles for gpredict feedback
        if self.pred_conn_state == 2:
            return self.cur_az, self.cur_el
        #self.update_predict_status()

    def predict_timeout(self):
        self.update_predict_status()

    def update_predict_status(self):
        if self.pred_conn_state == 0: #Disconnected
            self.predict_button.setText('Connect')
            self.pred_status_lbl.setText("Disconnected")
            self.pred_status_lbl.setStyleSheet("QLabel {  font-weight:bold; color:rgb(255,0,0) ; }")
            #self.gpredict_ip_le.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
            #self.gpredict_port_le.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
            self.gpredict_ip_le.setEnabled(True)
            self.gpredict_port_le.setEnabled(True)
        elif self.pred_conn_state == 1: #Listening
            self.predict_button.setText('Disconnect')
            self.pred_status_lbl.setText("Listening...")
            self.pred_status_lbl.setStyleSheet("QLabel {  font-weight:bold; color:rgb(255,255,0) ; }")
            #self.gpredict_ip_le.setStyleSheet("QLineEdit {background-color:rgb(225,225,225); color:rgb(0,0,0);}")
            #self.gpredict_port_le.setStyleSheet("QLineEdit {background-color:rgb(225,225,225); color:rgb(0,0,0);}")
            self.gpredict_ip_le.setEnabled(False)
            self.gpredict_port_le.setEnabled(False)
        elif self.pred_conn_state == 2: #Connected
            self.predict_button.setText('Disconnect')
            self.pred_status_lbl.setText("Connected")
            self.pred_status_lbl.setStyleSheet("QLabel {  font-weight:bold; color:rgb(0,255,0) ; }")
            #self.gpredict_ip_le.setStyleSheet("QLineEdit {background-color:rgb(225,225,225); color:rgb(0,0,0);}")
            #self.gpredict_port_le.setStyleSheet("QLineEdit {background-color:rgb(225,225,225); color:rgb(0,0,0);}")
            self.gpredict_ip_le.setEnabled(False)
            self.gpredict_port_le.setEnabled(False)
    #---- END GPREDICT and AUTO TRACK FUNCTIONS -----
    #
    #
    ##### ANTENNA CONTROL GET FUNCTIONS #####
    # Functions that QUERY the Daemon State and Position and update GUI displays

    def query_button_event(self):
        print self.utc_ts() + "Sending MANAGEMENT QUERY"
        if self.connected == True:
            self.connected, valid, state = self.callback.get_daemon_state(True)
            
        if self.connected == True:
            if valid == True:  self.set_daemon_state(state)
            if self.daemon_state == 'ACTIVE':
                print self.utc_ts() + "Sending MOTION QUERY"
                self.connected, valid, az, el, az_rate, el_rate = self.callback.get_motion_feedback(True)
                if valid == True:
                    self.cur_az = az
                    self.cur_el = el
                    self.cur_az_rate = az_rate
                    self.cur_el_rate = el_rate
                    self.update_current_angles()
                else:
                    self.auto_query_cb.setCheckState(QtCore.Qt.Unchecked)
        elif self.connected == False:
            self.update_connection_state()

    def auto_query_timeout(self):
        #print self.utc_ts() + "Sending MANAGEMENT QUERY"
        #this function is called when update_timer timesout.
        #update_timer is dormant if not connected
        if self.connected == True:
            self.connected, valid, state = self.callback.get_daemon_state(False)
            
        if self.connected == True:
            if valid == True:  self.set_daemon_state(state)
            if self.daemon_state == 'ACTIVE':
                #print self.utc_ts() + "Sending MOTION QUERY"
                self.connected, valid, az, el, az_rate, el_rate = self.callback.get_motion_feedback(False)
                if valid == True:
                    self.cur_az = az
                    self.cur_el = el
                    self.cur_az_rate = az_rate
                    self.cur_el_rate = el_rate
                    self.update_current_angles()
                else:
                    self.auto_query_cb.setCheckState(QtCore.Qt.Unchecked)
        elif self.connected == False:
            self.update_connection_state()

    def update_current_angles(self):
        self.az_compass.set_cur_az(self.cur_az)
        self.az_lcd_fr.set_cur(self.cur_az)
        self.az_lcd_fr.set_rate(self.cur_az_rate)

        self.el_compass.set_cur_el(self.cur_el)
        self.el_lcd_fr.set_cur(self.cur_el)
        self.el_lcd_fr.set_rate(self.cur_el_rate)

    def auto_query_cb_event(self, state):
        CheckState = (state == QtCore.Qt.Checked)
        if CheckState == True:  
            self.update_timer.start()
            print self.utc_ts() + "Started Auto Update, Interval: " + str(self.update_rate) + " [s]"
        else:
            self.update_timer.stop()
            print self.utc_ts() + "Stopped Auto Update"

    def update_feedback_rate(self):
        self.update_rate = float(self.fb_query_rate_le.text())    #Feedback Query Auto Update Interval in milliseconds

    #---- END ANTENNA CONTROL GET FUNCTIONS -----
    #
    #
    ##### ANTENNA CONTROL SET FUNCTIONS #####
    # Functions that update the TARGET ANGLE and send commands to the Daemon
    def stop_button_event(self):
        self.update_target_azimuth()
        self.update_target_elevation()
        self.callback.set_stop()

    def home_button_event(self):
        self.tar_az = self.home_az
        self.tar_el = self.home_el
        self.update_target_azimuth()
        self.update_target_elevation()
        self.callback.set_position(self.tar_az, self.tar_el, True)

    def update_button_event(self):
        self.tar_az = float(self.azTextBox.text())
        self.tar_el = float(self.elTextBox.text())
        self.update_target_azimuth()
        self.update_target_elevation()
        self.callback.set_position(self.tar_az, self.tar_el, True)

    def increment_target_angle(self, az_el, val):
        #Called by button control frame
        if az_el == 'az':
            self.tar_az += val
            self.update_target_azimuth()
        elif az_el == 'el':
            self.tar_el += val
            self.update_target_elevation()
        self.callback.set_position(self.tar_az, self.tar_el, True)

    def update_target_azimuth(self):
        if self.tar_az < -180.0: self.tar_az = -180.0
        if self.tar_az >  540.0: self.tar_az = 540.0
        self.az_compass.set_tar_az(self.tar_az)
        self.az_lcd_fr.set_tar(self.tar_az)
        self.azTextBox.setText(str(self.tar_az))

    def update_target_elevation(self):
        if self.tar_el < 0: self.tar_el = 0
        if self.tar_el > 180: self.tar_el = 180
        self.el_compass.set_tar_el(self.tar_el)
        self.el_lcd_fr.set_tar(self.tar_el)
        self.elTextBox.setText(str(self.tar_el))

    #---- END ANTENNA CONTROL SET FUNCTIONS -----
    #
    #
    ##### CONNECTION FRAME CONTROL FUNCTIONS #####
    # Button Events, SSID Update, UID update, DAEMON session state control
    def update_uid_event(self):
        pass

    def update_ssid_event(self, idx):
        if   idx == 0: #VUL
            self.ssid = 'VUL'
            self.port = 2000
            self.home_az = 180
            self.home_el = 0.0
        elif idx == 1: #3M0
            self.ssid = '3M0'
            self.port = 2001
            self.home_az = 180
            self.home_el = 90.0
        elif idx == 2: #4M5
            self.ssid = '4M5'
            self.port = 2002
        elif idx == 3: #WX
            self.ssid = 'WX'
            self.port = 2003
        print self.utc_ts() + "Updated Subsystem ID: " + self.ssid
        print self.utc_ts() + "Updated Daemon port number: " + str(self.port)
        self.callback.set_ssid(self.ssid)
        self.callback.set_port(self.port)

    def connect_button_event(self):
        if self.connected == False:
            print self.utc_ts() + "Connecting to Daemon..."
            self.connected = self.callback.connect(self.ip, self.port,self)
        elif self.connected == True:
            print self.utc_ts() + "Disconnecting from Daemon..."
            self.connected = self.callback.disconnect()
            self.set_daemon_state('IDLE')
        self.update_connection_state()

    def update_connection_state(self):
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
            self.update_timer.start()
        elif self.connected == False:
            self.connect_button.setText('Connect')
            self.conn_status_lbl.setText('DISCONNECTED')
            self.conn_status_lbl.setStyleSheet("QLabel {font-weight:bold; color:rgb(255,0,0);}")
            self.ssid_combo.setEnabled(True)
            self.uid_tb.setEnabled(True)
            self.session_button.setEnabled(False)
            self.set_daemon_state('IDLE')
            self.update_timer.stop()

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
        elif self.daemon_state == 'FAULT':
            self.daemon_state_lbl.setStyleSheet("QLabel {font-weight:bold; color:rgb(255,0,0);}")
            self.session_button.setText('Stop')
            self.ctrl_fr.setEnabled(True)

    def session_button_event(self):
        #USer is attempting to start a tracking session
        #is the daemon in a STANDBY State?
        if self.daemon_state == 'STANDBY':
            print self.utc_ts() + "Requesting Session START"
            self.callback.set_session_start()
            #self.session_button.setText('Stop')
        elif self.daemon_state == 'ACTIVE':
            print self.utc_ts() + "Requesting Session STOP"
            self.callback.set_session_stop()

    #**** END CONNECTION FRAME CONTROL FUNCTIONS *****
    #
    #
    ##### USER INTERFACE CONTROL SETUP #####

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
        self.gpredict_ip_le = QtGui.QLineEdit()
        self.gpredict_ip_le.setText(self.pred_ip)
        self.gpredict_ip_le.setInputMask("000.000.000.000;")
        self.gpredict_ip_le.setEchoMode(QtGui.QLineEdit.Normal)
        self.gpredict_ip_le.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.gpredict_ip_le.setMaxLength(15)
        self.gpredict_ip_le.setFixedHeight(20)

        self.gpredict_port_le = QtGui.QLineEdit()
        self.gpredict_port_le.setText(str(self.pred_port))
        self.port_validator = QtGui.QIntValidator()
        self.port_validator.setRange(0,65535)
        self.gpredict_port_le.setValidator(self.port_validator)
        self.gpredict_port_le.setEchoMode(QtGui.QLineEdit.Normal)
        self.gpredict_port_le.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.gpredict_port_le.setMaxLength(5)
        self.gpredict_port_le.setFixedWidth(50)
        self.gpredict_port_le.setFixedHeight(20)

        label = QtGui.QLabel('Status:')
        label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        label.setStyleSheet("QLabel {color:rgb(255,255,255);}")
        label.setFixedHeight(10)
        self.pred_status_lbl = QtGui.QLabel('Disconnected')
        self.pred_status_lbl.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.pred_status_lbl.setStyleSheet("QLabel {font-weight:bold; color:rgb(255,0,0);}")
        self.pred_status_lbl.setFixedWidth(125)
        self.pred_status_lbl.setFixedHeight(10)

        self.predict_button = QtGui.QPushButton("Start Predict Server")
        self.predict_button.setFixedHeight(20)

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

        self.auto_track_cb = QtGui.QCheckBox("Auto Track")  
        self.auto_track_cb.setStyleSheet("QCheckBox { background-color:rgb(0,0,0); color:rgb(255,255,255); }")
        self.auto_track_cb.setFixedHeight(20)

        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.gpredict_ip_le)
        hbox1.addWidget(self.gpredict_port_le)

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
        hbox5.addWidget(self.auto_track_cb)
        hbox5.addLayout(vbox1)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addWidget(self.predict_button)
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


    
