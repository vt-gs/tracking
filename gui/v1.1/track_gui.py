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

class MainWindow(QtGui.QMainWindow):
    def __init__(self, ip, port):
        #QtGui.QMainWindow.__init__(self)
        super(MainWindow, self).__init__()
        self.resize(700, 650)
        self.setMinimumWidth(600)
        self.setMaximumWidth(850)
        self.setMinimumHeight(500)
        self.setMaximumHeight(700)
        self.setWindowTitle('VTGS Tracking GUI v1.1')
        self.setContentsMargins(0,0,0,0)
        self.main_window = main_widget()
        self.setCentralWidget(self.main_window)

        self.cur_az = 0
        self.tar_az = 0
        self.cur_el = 0
        self.tar_el = 0
        self.home_az = 0.0
        self.home_el = 0.0

        self.callback    = None   #Callback accessor for tracking control
        self.connected   = False  #Status of TCP/IP connection to MD-01
        self.update_rate = 250    #Feedback Query Auto Update Interval in milliseconds
        self.autoTrack = False      #auto track mode, True = Auto, False = Manual

        self.statusBar().showMessage("| Disconnected | Manual | Current Az: 000.0 | Current El: 000.0 |")

        self.initUI()
        self.darken()
        self.setFocus()

    def initUI(self):
        self.initFrames()
        self.initDials()
        self.initTabControl()
        self.initMainTab()
        self.initCalTab()

        #self.connectSignals()
        self.show()

    def initFrames(self):
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

        self.main_window.grid.addWidget(self.az_dial_fr,0,0,1,1)
        self.main_window.grid.addWidget(self.az_ctrl_fr,1,0,1,1)
        self.main_window.grid.addWidget(self.el_dial_fr,0,1,1,1)
        self.main_window.grid.addWidget(self.el_ctrl_fr,1,1,1,1)

    def initDials(self):
        self.el_compass = el_QwtDial(self.el_dial_fr_grid)
        self.az_compass = az_QwtDial(self.az_dial_fr_grid)
    
    def initTabControl(self):
        self.tabs = QtGui.QTabWidget()
        self.tabs.setTabPosition(QtGui.QTabWidget.South)

        self.main_tab = QtGui.QWidget()	
        self.main_tab.grid = QtGui.QGridLayout()
        self.tabs.addTab(self.main_tab,"Manual")
        self.main_tab.setAutoFillBackground(True)
        p = self.main_tab.palette()
        p.setColor(self.main_tab.backgroundRole(), QtCore.Qt.black)        
        self.main_tab.setPalette(p)

        self.auto_tab = QtGui.QWidget()	
        self.auto_tab.grid = QtGui.QGridLayout()
        self.tabs.addTab(self.auto_tab,"Auto")
        self.auto_tab.setAutoFillBackground(True)
        p = self.auto_tab.palette()
        p.setColor(self.auto_tab.backgroundRole(), QtCore.Qt.black)        
        self.auto_tab.setPalette(p)
        
        self.cal_tab = QtGui.QWidget()	
        self.cal_tab.grid = QtGui.QGridLayout()
        self.tabs.addTab(self.cal_tab,"Cal")
        self.cal_tab.setAutoFillBackground(True)
        p = self.cal_tab.palette()
        p.setColor(self.cal_tab.backgroundRole(), QtCore.Qt.black)        
        self.cal_tab.setPalette(p)

        self.net_tab = QtGui.QWidget()	
        self.net_tab_grid = QtGui.QGridLayout()
        self.tabs.addTab(self.net_tab,"Config")
        self.net_tab.setAutoFillBackground(True)
        p = self.net_tab.palette()
        p.setColor(self.net_tab.backgroundRole(), QtCore.Qt.black)        
        self.net_tab.setPalette(p)

        self.main_window.grid.addWidget(self.tabs,2,0,1,2)
        self.main_window.grid.setRowStretch(0,1)

    def initMainTab(self):
        #Init Az Increment Control
        self.initAzControls()
        #Init El Increment Control
        self.initElControls()
        #Init Direct Motor Drive Controls
        self.initMotorCtrl()
        #Init Entry Box Controls
        self.initEntryBoxControls()
        #Init Feedback Query Controls
        self.initFeedbackQuery()

        self.main_tab_grid = QtGui.QGridLayout()
        self.main_tab_grid.addWidget(self.entry_fr   ,0,0,3,1)
        self.main_tab_grid.addWidget(self.fb_query_fr,0,1,3,1)
        self.main_tab_grid.addWidget(self.dir_fr     ,0,2,3,1)
        self.main_tab_grid.setColumnStretch(3,10)
        self.main_tab.setLayout(self.main_tab_grid)

    def initAzControls(self):
        self.azMinusTenButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azMinusTenButton.setText("-10.0")
        self.azMinusTenButton.setFixedWidth(45)

        self.azMinusOneButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azMinusOneButton.setText("-1.0")
        self.azMinusOneButton.setFixedWidth(45)

        self.azMinusPtOneButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azMinusPtOneButton.setText("-0.1")
        self.azMinusPtOneButton.setFixedWidth(45)

        self.azStopButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azStopButton.setText("STOP!")
        self.azStopButton.setFixedWidth(45)

        self.azPlusPtOneButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azPlusPtOneButton.setText("+0.1")
        self.azPlusPtOneButton.setFixedWidth(45)

        self.azPlusOneButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azPlusOneButton.setText("+1.0")
        self.azPlusOneButton.setFixedWidth(45)

        self.azPlusTenButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.azPlusTenButton.setText("+10.0")
        self.azPlusTenButton.setFixedWidth(45)

        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.azMinusTenButton)
        hbox1.addWidget(self.azMinusOneButton)
        hbox1.addWidget(self.azMinusPtOneButton)
        hbox1.addWidget(self.azStopButton)
        hbox1.addWidget(self.azPlusPtOneButton)
        hbox1.addWidget(self.azPlusOneButton)
        hbox1.addWidget(self.azPlusTenButton)
        self.az_ctrl_fr.setLayout(hbox1)

    def initElControls(self):
        self.elMinusTenButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elMinusTenButton.setText("-10.0")
        self.elMinusTenButton.setFixedWidth(45)

        self.elMinusOneButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elMinusOneButton.setText("-1.0")
        self.elMinusOneButton.setFixedWidth(45)

        self.elMinusPtOneButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elMinusPtOneButton.setText("-0.1")
        self.elMinusPtOneButton.setFixedWidth(45)

        self.elStopButton = QtGui.QPushButton(self.az_ctrl_fr)
        self.elStopButton.setText("STOP!")
        self.elStopButton.setFixedWidth(45)

        self.elPlusPtOneButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elPlusPtOneButton.setText("+0.1")
        self.elPlusPtOneButton.setFixedWidth(45)
        
        self.elPlusOneButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elPlusOneButton.setText("+1.0")
        self.elPlusOneButton.setFixedWidth(45)

        self.elPlusTenButton = QtGui.QPushButton(self.el_ctrl_fr)
        self.elPlusTenButton.setText("+10.0")
        self.elPlusTenButton.setFixedWidth(45)

        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.elMinusTenButton)
        hbox1.addWidget(self.elMinusOneButton)
        hbox1.addWidget(self.elMinusPtOneButton)
        hbox1.addWidget(self.elStopButton)
        hbox1.addWidget(self.elPlusPtOneButton)
        hbox1.addWidget(self.elPlusOneButton)
        hbox1.addWidget(self.elPlusTenButton)
        self.el_ctrl_fr.setLayout(hbox1)

    def initMotorCtrl(self):
        self.dir_fr = QtGui.QFrame(self)
        self.dir_fr.setFrameShape(QtGui.QFrame.StyledPanel)
       
        self.motor_lbl = QtGui.QLabel("     Direct Motor Drive     ")
        self.motor_lbl.setAlignment(QtCore.Qt.AlignCenter|QtCore.Qt.AlignVCenter)
        self.motor_lbl.setStyleSheet("QLabel {text-decoration:underline; color:rgb(255,255,255);}")

        self.UpLeftButton = QtGui.QPushButton("U+L")
        self.UpLeftButton.setFixedWidth(50)
        self.UpButton = QtGui.QPushButton("Up")
        self.UpButton.setFixedWidth(50)
        self.UpRightButton = QtGui.QPushButton("U+R")
        self.UpRightButton.setFixedWidth(50)
        self.LeftButton = QtGui.QPushButton("Left")
        self.LeftButton.setFixedWidth(50)
        self.StopButton = QtGui.QPushButton("STOP!")
        self.StopButton.setFixedWidth(50)
        self.RightButton = QtGui.QPushButton("Right")
        self.RightButton.setFixedWidth(50)
        self.DnLeftButton = QtGui.QPushButton("D+L")
        self.DnLeftButton.setFixedWidth(50)
        self.DownButton = QtGui.QPushButton("Down")
        self.DownButton.setFixedWidth(50)
        self.DnRightButton = QtGui.QPushButton("D+R")
        self.DnRightButton.setFixedWidth(50)

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
    
    def initEntryBoxControls(self):
        self.updateButton = QtGui.QPushButton("Update")

        self.azLabel = QtGui.QLabel("Azimuth:")
        self.azLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.azLabel.setStyleSheet("QLabel {color:rgb(0,0,255);}")

        self.azTextBox = QtGui.QLineEdit()
        self.azTextBox.setText("000.0")
        self.azTextBox.setInputMask("#000.0;")
        self.azTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.azTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.azTextBox.setMaxLength(6)
        self.azTextBox.setFixedWidth(60)

        self.elLabel = QtGui.QLabel("Elevation:")
        self.elLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.elLabel.setStyleSheet("QLabel {color:rgb(0,0,255);}")

        self.elTextBox = QtGui.QLineEdit(self.el_dial_fr)
        self.elTextBox.setText("000.0")
        self.elTextBox.setInputMask("000.0;")
        self.elTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.elTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.elTextBox.setMaxLength(6)
        self.elTextBox.setFixedWidth(60)

        self.entry_fr = QtGui.QFrame(self)
        self.entry_fr.setFrameShape(QtGui.QFrame.StyledPanel)

        az_hbox = QtGui.QHBoxLayout()
        az_hbox.addWidget(self.azLabel)
        az_hbox.addWidget(self.azTextBox)

        el_hbox = QtGui.QHBoxLayout()
        el_hbox.addWidget(self.elLabel)
        el_hbox.addWidget(self.elTextBox)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(az_hbox)
        vbox.addLayout(el_hbox)
        vbox.addWidget(self.updateButton)
        self.entry_fr.setLayout(vbox)

    def initFeedbackQuery(self):
        self.fb_query_fr = QtGui.QFrame(self)
        self.fb_query_fr.setFrameShape(QtGui.QFrame.StyledPanel)
        
        self.fb_interval_lbl = QtGui.QLabel("Interval [s]:")
        self.fb_interval_lbl.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.fb_interval_lbl.setStyleSheet("QLabel {color:rgb(255,255,255);}")

        self.fb_query_rate_le = QtGui.QLineEdit()
        self.fb_query_rate_le.setText("0.25")
        self.query_val = QtGui.QDoubleValidator()
        self.fb_query_rate_le.setValidator(self.query_val)
        self.fb_query_rate_le.setEchoMode(QtGui.QLineEdit.Normal)
        self.fb_query_rate_le.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.fb_query_rate_le.setMaxLength(4)
        self.fb_query_rate_le.setFixedWidth(50)

        self.autoQuery_cb = QtGui.QCheckBox("Auto Query")  
        self.autoQuery_cb.setStyleSheet("QCheckBox { background-color:rgb(0,0,0); color:rgb(255,0,0); }")

        self.queryButton  = QtGui.QPushButton("Query")

        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.fb_interval_lbl)
        hbox1.addWidget(self.fb_query_rate_le)
        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.autoQuery_cb)
        vbox.addLayout(hbox1)
        vbox.addWidget(self.queryButton)
        self.fb_query_fr.setLayout(vbox)

    def initNetTab(self):
        pass
        #Init MD01 Connection Frame
        #self.initMD01Connection()
        #Init Predict Connection Frame
        #self.initPredictConnection()
        
        
    
    def initCalTab(self):
        #Init Set Angles
        self.initCalAnglesControls()
        #Init Motor Power Control
        self.initMotorPower()   
        
        self.cal_tab_grid = QtGui.QGridLayout()
        self.cal_tab_grid.addWidget(self.cal_angle_fr,0,0,3,1)
        self.cal_tab_grid.addWidget(self.mot_power_fr,0,1,3,1)
        self.cal_tab_grid.setColumnStretch(3,10)
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

    

    

    


    def initControls(self):
        self.updateButton = QtGui.QPushButton("Update")
        self.queryButton  = QtGui.QPushButton("Query")
        self.homeButton   = QtGui.QPushButton("Home")
        self.stopButton   = QtGui.QPushButton("STOP!")
        
        self.autoQuery_cb = QtGui.QCheckBox("Auto Query")  #Automatically update ADC voltages checkbox option
        self.autoQuery_cb.setStyleSheet("QCheckBox { font-size: 12px; \
                                                    background-color:rgb(0,0,0); \
                                                    color:rgb(255,255,255); }")

        self.autoUpdate_cb = QtGui.QCheckBox("Auto Update")  #Automatically update ADC voltages checkbox option
        self.autoUpdate_cb.setStyleSheet("QCheckBox { font-size: 12px; \
                                                    background-color:rgb(0,0,0); \
                                                    color:rgb(255,255,255); }")

        self.autoTrack_cb = QtGui.QCheckBox("Auto Track")  #Automatically update ADC voltages checkbox option
        self.autoTrack_cb.setStyleSheet("QCheckBox { font-size: 12px; \
                                                    background-color:rgb(0,0,0); \
                                                    color:rgb(255,255,255); }")

        self.azLabel = QtGui.QLabel("Azimuth:")
        self.azLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.azLabel.setStyleSheet("QLabel {color:rgb(0,0,255);}")

        self.azTextBox = QtGui.QLineEdit()
        self.azTextBox.setText("000.0")
        self.azTextBox.setInputMask("#000.0;")
        self.azTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.azTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.azTextBox.setMaxLength(6)
        self.azTextBox.setFixedWidth(60)

        self.elLabel = QtGui.QLabel("Elevation:")
        self.elLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.elLabel.setStyleSheet("QLabel {color:rgb(0,0,255);}")

        self.elTextBox = QtGui.QLineEdit(self.el_dial_fr)
        self.elTextBox.setText("000.0")
        self.elTextBox.setInputMask("000.0;")
        self.elTextBox.setEchoMode(QtGui.QLineEdit.Normal)
        self.elTextBox.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.elTextBox.setMaxLength(6)
        self.elTextBox.setFixedWidth(60)

        self.update_fr = QtGui.QFrame(self)
        self.update_fr.setFrameShape(QtGui.QFrame.StyledPanel)

        #tar_ang_lbl = QtGui.QLabel("Target Angle Entry")
        #palette = QtGui.QPalette(self.palette())
        #palette.setColor(palette.Background,QtCore.Qt.transparent)
        #palette.setColor(palette.Foreground,QtGui.QColor(0,0,255))
        #tar_ang_lbl.setPalette(palette)
        #font = QtGui.QFont()
        #font.setBold(True)
        #font.setPixelSize(16)
        #font.setUnderline(True)
        #tar_ang_lbl.setFont(font)        

        az_hbox = QtGui.QHBoxLayout()
        az_hbox.addWidget(self.azLabel)
        az_hbox.addWidget(self.azTextBox)

        el_hbox = QtGui.QHBoxLayout()
        el_hbox.addWidget(self.elLabel)
        el_hbox.addWidget(self.elTextBox)

        vbox = QtGui.QVBoxLayout()
        vbox.addStretch(1)
        #vbox.addWidget(tar_ang_lbl)
        vbox.addLayout(az_hbox)
        vbox.addLayout(el_hbox)
        vbox.addWidget(self.updateButton)
        #vbox.addWidget(self.autoQuery_cb)
        self.update_fr.setLayout(vbox)


        self.auto_fr = QtGui.QFrame(self)
        self.auto_fr.setFrameShape(QtGui.QFrame.StyledPanel)
        vbox = QtGui.QVBoxLayout()
        #vbox.addStretch(1)
        #vbox.addWidget(tar_ang_lbl)
        vbox.addWidget(self.autoQuery_cb)
        vbox.addWidget(self.autoUpdate_cb)
        vbox.addWidget(self.autoTrack_cb)
        self.auto_fr.setLayout(vbox)

        self.updateTimer = QtCore.QTimer(self)
        self.updateTimer.setInterval(self.update_rate)

    def initConfig(self):
        self.update_rate_le = QtGui.QLineEdit()
        self.update_rate_le.setText("0.25")
        self.update_val = QtGui.QDoubleValidator()
        self.update_rate_le.setValidator(self.update_val)
        self.update_rate_le.setEchoMode(QtGui.QLineEdit.Normal)
        self.update_rate_le.setStyleSheet("QLineEdit {background-color:rgb(255,255,255); color:rgb(0,0,0);}")
        self.update_rate_le.setMaxLength(4)
        self.update_rate_le.setFixedWidth(50)

    def setCallback(self, callback):
        self.callback = callback
    
    def setPredictCallback(self, callback):
        self.pred_cb = callback
        #sat_list = self.pred_cb.get_sat_list()
        #print sat_list

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

    def darken(self):
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background,QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.WindowText,QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.Text,QtCore.Qt.white)
        self.setPalette(palette)

    def getTimeStampGMT(self):
        return str(date.utcnow()) + " GMT | "

