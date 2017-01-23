#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, platform
from PyQt5 import QtWidgets, QtCore, QtGui

from theatre.TrayIcon import TrayIcon
from theatre.TheatreModel import Shedule
from theatre.Preferences import Preferences, is_windows
from theatre.MainWindow import CURRENT_PATH

DB_FILENAME = "shedule.db" # filename for database

class TheatreApplication(QtWidgets.QApplication):

    """
    Creates all application components.

    """
    def __init__(self, *args):
        QtWidgets.QApplication.__init__(self, *args)
        self.setQuitOnLastWindowClosed(False) # it should work in the system tray
        self.aboutToQuit.connect(self.on_quit)
        self.setIconTheme()
        prefs = Preferences() # application preferences
        self.shedule = Shedule(prefs.at_home(DB_FILENAME)) # create a database object
        self.trayicon = TrayIcon(self.shedule) # create tray icon
        self.trayicon.show()

    @staticmethod
    def setIconTheme():

        """
        Sets icon theme in Windows.

        """
        if is_windows():
            path = os.sep.join([CURRENT_PATH, 'icons'])
            QtGui.QIcon.setThemeSearchPaths([path])
            QtGui.QIcon.setThemeName('black_white_2_gloss')

    @QtCore.pyqtSlot()
    def on_quit(self):

        """
        Closes the database before quitting.

        """
        self.shedule.close()

def start():

    """
    The main entry point of the program.

    """
    app = TheatreApplication(sys.argv)
    sys.exit(app.exec_())
