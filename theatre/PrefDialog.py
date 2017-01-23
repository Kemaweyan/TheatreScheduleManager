#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets, QtGui
from datetime import timedelta

from theatre.Preferences import Preferences


def createIntervalText(value):

    """
    Creates a text for time intervals.

    """
    def is_plural(num):

        """
        Adds plural suffix 's' if value is plural.

        """
        if num > 1:
            return 's'
        return ''

    text = ''
    td = timedelta(seconds=value)
    # timedelta contains fields with days and seconds (less than 1 day)
    # but there is not hours and minutes, so calculate them:
    hours = td.seconds // 3600 # hours count
    minutes = td.seconds // 60 % 60 # minutes count
    seconds = td.seconds % 3600 % 60 # seconds count
    if td.days > 0:
        # there is days in the interval, add days count
        text += '{0} day{1} '.format(td.days, is_plural(td.days))
    if hours > 0:
        # there is hours in the interval, add hours count
        text += '{0} hour{1} '.format(hours, is_plural(hours))
    if minutes > 0:
        # there is minutes in the interval, add minutes count
        text += '{0} minute{1} '.format(minutes, is_plural(minutes))
    if seconds > 0:
        # there is seconds in the interval, add seconds count
        text += '{0} second{1} '.format(seconds, is_plural(seconds))
    return text.strip() # remove last space symblol




class PrefDialog(QtWidgets.QDialog):

    """
    Changes preferences.

    """
    # the signal emitted when preferencces has been changed
    pref_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        self.setModal(True) # block parent window
        self.setMinimumSize(280, 120)
        self.preferences = Preferences()

        # get synchronization interval
        sync_interval = self.preferences['SYNC']['sync_interval']

        # create a widget for interval
        # and fill it with standard values
        self.intervalEdit = QtWidgets.QComboBox()
        self.intervalEdit.addItem('30 minutes', 1800)
        self.intervalEdit.addItem('1 hour', 3600)
        self.intervalEdit.addItem('2 hours', 7200)
        self.intervalEdit.addItem('5 hours', 18000)
        # select an item matching to interval
        index = self.intervalEdit.findData(sync_interval)
        if index < 0: # matching item not found
            # then add an item with custom interval
            self.intervalEdit.addItem(createIntervalText(sync_interval), sync_interval)
            # and select it
            index = self.intervalEdit.count() - 1
        # set selected item in the widget
        self.intervalEdit.setCurrentIndex(index)

        # attach widgets to layout
        form = QtWidgets.QFormLayout()
        form.addRow('Sync interval', self.intervalEdit)

        # create control buttons
        self.okBtn = QtWidgets.QPushButton('OK')
        self.okBtn.clicked.connect(self.on_accept)
        self.cancelBtn = QtWidgets.QPushButton('Cancel')
        self.cancelBtn.clicked.connect(self.reject)

        # add buttons to layout
        btnBox = QtWidgets.QHBoxLayout()
        btnBox.addStretch()
        btnBox.addWidget(self.okBtn)
        btnBox.addWidget(self.cancelBtn)

        # add layouts to main layout
        mainBox = QtWidgets.QVBoxLayout()
        mainBox.addLayout(form)
        mainBox.addStretch()
        mainBox.addLayout(btnBox)

        # set layout to the window
        self.setLayout(mainBox)

    @QtCore.pyqtSlot()
    def on_accept(self):

        """
        Called when OK button was pressed.

        """
        # get values from widgets
        self.preferences['SYNC']['sync_interval'] = self.intervalEdit.currentData()
        self.preferences.save() # save preferences
        self.pref_changed.emit() # emit changed signal
        self.accept() # set 'accept' code


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dialog = PrefDialog()
    dialog.show()
    sys.exit(app.exec_())
