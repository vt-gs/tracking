#!/usr/bin/env python
#########################################
#   Title: VTGS Tracking GUI            #
# Project: VTGS                         #
# Version: 1.0                          #
#    Date: July 24, 2016                #
#  Author: Zach Leffke, KJ4QLP          #
# Comment: Angle Increment Control 
#           Buttons                     # 
#########################################

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import Qt
import PyQt4.Qwt5 as Qwt

class control_button_frame(QtGui.QFrame):
    def __init__(self, parent=None):
        super(control_button_frame, self).__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.initWidgets()

    def initWidgets(self):
        self.MinusTenButton = QtGui.QPushButton(self)
        self.MinusTenButton.setText("-10.0")
        self.MinusTenButton.setMinimumWidth(45)

        self.MinusOneButton = QtGui.QPushButton(self)
        self.MinusOneButton.setText("-1.0")
        self.MinusOneButton.setMinimumWidth(45)

        self.MinusPtOneButton = QtGui.QPushButton(self)
        self.MinusPtOneButton.setText("-0.1")
        self.MinusPtOneButton.setMinimumWidth(45)

        self.PlusPtOneButton = QtGui.QPushButton(self)
        self.PlusPtOneButton.setText("+0.1")
        self.PlusPtOneButton.setMinimumWidth(45)

        self.PlusOneButton = QtGui.QPushButton(self)
        self.PlusOneButton.setText("+1.0")
        self.PlusOneButton.setMinimumWidth(45)

        self.PlusTenButton = QtGui.QPushButton(self)
        self.PlusTenButton.setText("+10.0")
        self.PlusTenButton.setMinimumWidth(45)

        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.MinusTenButton)
        hbox1.addWidget(self.MinusOneButton)
        hbox1.addWidget(self.MinusPtOneButton)
        hbox1.addWidget(self.PlusPtOneButton)
        hbox1.addWidget(self.PlusOneButton)
        hbox1.addWidget(self.PlusTenButton)
        self.setLayout(hbox1)

