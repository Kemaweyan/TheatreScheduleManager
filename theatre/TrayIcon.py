#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from datetime import datetime
import calendar

from theatre.MainWindow import MainWindow, ICON_DEFAULT, ICON_NEW
from theatre.TheatreModel import Event
from theatre.Sync import SyncThread
from theatre.Preferences import Preferences
from theatre.PrefDialog import PrefDialog

class TrayMenu(QtWidgets.QMenu):

    """
    The tray-icon menu.

    """
    def __init__(self, parent=None):
        QtWidgets.QMenu.__init__(self, parent)

        self.show_action = self.addAction("Show Theatre") # show/hide the main window
        self.show_action.setCheckable(True)
        self.show_action.setChecked(False) # the main window is hidden by default
        self.addSeparator()
        self.sync_action = self.addAction(QtGui.QIcon.fromTheme('reload'), "Sync all") # sync shedule
        self.settings_action = self.addAction(QtGui.QIcon.fromTheme('gtk-preferences'), "Preferences") # show settings window
        self.addSeparator()
        self.quit_action = self.addAction(QtGui.QIcon.fromTheme('exit'), "Quit") # quit program

    @QtCore.pyqtSlot(bool)
    def on_visibility_changed(self, visible):

        """
        Called when visibility of MainWindow changes.

        """
        self.show_action.setChecked(visible)



class TrayIcon(QtWidgets.QSystemTrayIcon):

    """
    System tray icon object.

    """
    tooltip_text = 'Theatre Shedule Manager'
    tooltip_text_new = 'Theatre Shedule Manager - new events'

    def __init__(self, shedule, parent=None):
        QtWidgets.QWidget.__init__(self, QtGui.QIcon(ICON_DEFAULT), parent)

        self.shedule = shedule # save database
        self.activated.connect(self.on_activated)

        self.menu = TrayMenu()
        self.menu.show_action.triggered.connect(self.on_show_theatre)
        self.menu.sync_action.triggered.connect(self.on_sync)
        self.menu.settings_action.triggered.connect(self.on_settings)
        self.menu.quit_action.triggered.connect(self.on_quit)

        self.main_window = None # do not create MainWindow at startup
        self.thread = None # syncronization thread
        self.manual_sync = False # is synchronization called by user
        self.has_new = False # are there updates
        self.setToolTip(self.tooltip_text)

        prefs = Preferences()
        # start the timer for automatic sync
        self.timer_id = self.startTimer(prefs['SYNC']['sync_interval'] * 1000)

    @QtCore.pyqtSlot('QSystemTrayIcon::ActivationReason')
    def on_activated(self, reason):

        """
        Called when user clicked on tray icon.

        """
        if reason == self.Context: # right button
            self.menu.exec_(QtGui.QCursor.pos()) # show menu
        elif reason == self.Trigger: # left button
            self.on_show_theatre(not self.menu.show_action.isChecked()) #show/hide the main window

    @QtCore.pyqtSlot(bool)
    def on_show_theatre(self, checked=False):

        """
        Shows or hides the main window.

        """
        if checked: # the window shold be shown
            if self.main_window == None: # if the windows has not been created yet
                self.main_window = MainWindow(self.shedule) # create the window
                self.main_window.visible_signal.connect(self.menu.on_visibility_changed)
                self.main_window.pref_signal.connect(self.on_settings)
                self.main_window.sync_all_signal.connect(self.on_sync)
                self.main_window.quit_signal.connect(self.on_quit)
            self.main_window.show()
            if self.has_new: # if icon indicates that there are updates
                self.setIcon(QtGui.QIcon(ICON_DEFAULT)) # set default icon
                self.setToolTip(self.tooltip_text)
                self.has_new = False # and mark updates as seen
        elif self.main_window != None: # if the window has been created
            self.main_window.hide() # hide it

    def start_sync(self, manual=False):

        """
        Starts synchronization thread.

        """
        # Do nothing if thread already started.
        if self.thread:
            return
        self.manual_sync = manual # save manual start flag
        self.has_new = False # there are not updates yet
        self.setIcon(QtGui.QIcon(ICON_DEFAULT)) # set default icon
        self.setToolTip(self.tooltip_text)
        prefs = Preferences()
        self.thread = SyncThread() # create a sync thread
        self.thread.complete.connect(self.on_sync_complete)
        self.thread.failure.connect(self.on_sync_failure)
        self.thread.start()

    @QtCore.pyqtSlot(bool)
    def on_sync(self, checked=False):

        """
        Starts manual sinchronization.

        """
        self.start_sync(True)

    @QtCore.pyqtSlot()
    def timer_restart(self):

        """
        Applies new settings of synchronization interval.

        """
        prefs = Preferences()
        self.killTimer(self.timer_id) # stop old timer
        # and create new one
        self.timer_id = self.startTimer(prefs['SYNC']['sync_interval'] * 1000)

    def timerEvent(self, event):

        """
        Starts automatic synchronization.

        """
        self.start_sync()

    @QtCore.pyqtSlot(bool)
    def on_settings(self, checked=False):

        """
        Shows the setting window.

        """
        dialog = PrefDialog(self.main_window)
        dialog.pref_changed.connect(self.timer_restart)
        dialog.exec_()

    @QtCore.pyqtSlot()
    def on_quit(self):

        """
        Checks changes in shedule. Asks for saving changes.

        """
        if self.shedule.is_changed(): # if shedule has been changed
            # show message with question
            msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, 'Unsaved data', 'Some data has been changed. Save changes?', 
                    QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel, self.main_window)
            answer = msg_box.exec_()
            if answer == QtWidgets.QMessageBox.Save: #user pressed Save
                self.shedule.save_cache() # save changes
            elif answer == QtWidgets.QMessageBox.Cancel: # user pressed Dancel
                return # do nothing
            # if user pressed Discard - just quit program
        QtWidgets.qApp.quit()

    def show_message(self, message, icon):

        """
        Shows the synchronization report message.

        """
        if self.manual_sync: # if sinchronization was started manually
            # show message box
            msg_box = QtWidgets.QMessageBox(icon, 'Sync report', message, QtWidgets.QMessageBox.Ok, self.main_window)
            msg_box.exec_()
        elif self.has_new: # if there are updates
            # show message on the icon
            self.showMessage('Sync report', message)
            self.setIcon(QtGui.QIcon(ICON_NEW))
            self.setToolTip(self.tooltip_text_new)
        self.thread = None # remove thread object

    @QtCore.pyqtSlot('QDateTime', 'QByteArray')
    def on_sync_complete(self):

        """
        Calls when sinchronization succeed.
        Updates the model.

        """
        all_changes = {}
        self.thread.wait() # wait for thread ends
        for key, month in self.thread.events.items():
            model = self.shedule.get_month(key=key)
            changes = model.update(month)
            if changes:
                all_changes[key] = changes
                self.has_new = True

        if self.has_new: # there are new events
            message = '<b>Shedule has been successfully updated</b><br><br>'
            for key, changes in all_changes.items():
                month_num = int(key[-1:]) if key[4] == '0' else int(key[-2:])
                message += '{} {}<br>'.format(calendar.month_name[month_num], key[:4])
                message += '<br>'.join(changes) 
        elif self.thread.events: # there are old events only
            message = 'Shedule is up to date'
        else: # shedule is empty
            message = 'Shedule on the server is empty'

        self.show_message(message, QtWidgets.QMessageBox.Information)
        

    @QtCore.pyqtSlot('QDateTime', str)
    def on_sync_failure(self, msg):

        """
        Called when sinchronization failed.

        """
        message = 'An error has occurred when updating:\n' + msg
        self.show_message(message, QtWidgets.QMessageBox.Critical)
