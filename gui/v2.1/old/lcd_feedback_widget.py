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

class LCD(QtGui.QLCDNumber):    
    def __init__(self, parent=None, r=0,g=0,b=0):        
        super(LCD, self).__init__(parent)
        self.setSegmentStyle(QtGui.QLCDNumber.Flat)
        palette = QtGui.QPalette(self.palette())
        palette.setColor(palette.Background,QtCore.Qt.transparent)
        palette.setColor(palette.Foreground,QtGui.QColor(r,g,b))
        self.setPalette(palette)
        self.setFixedHeight(30)
        self.setFixedWidth(85)
        self.display(000.0)

class lcd_feedback_widget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(lcd_feedback_widget, self).__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        #self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.initWidgets()

    def initWidgets(self):
        self.cur_lcd  = LCD(self,255,0,0)
        self.rate_lcd = LCD(self,255,0,255)
        self.tar_lcd  = LCD(self,0,0,255)
        
        lcd_hbox = QtGui.QHBoxLayout()
        lcd_hbox.addWidget(self.cur_lcd)
        lcd_hbox.addWidget(self.rate_lcd)
        lcd_hbox.addWidget(self.tar_lcd)
        self.setLayout(lcd_hbox)

