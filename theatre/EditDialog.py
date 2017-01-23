#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets
from calendar import monthrange
from datetime import datetime, timedelta

from theatre.TheatreModel import Event, Month

class EditDialog(QtWidgets.QDialog):

    """
    Adds new or edits existing event.

    """
    def __init__(self, month, event=None, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        self.setModal(True) # block parent window
        self.setMinimumSize(350, 200)

        self.event = None # result event

        # event should belong to selected month in shedule
        mindate = month.date # minimum date is the first day of the month
        # maximum date is the last day of the month
        maxdate = datetime(month.date.year, month.date.month, monthrange(month.date.year, month.date.month)[1])

        # create widgets
        self.dateEdit = QtWidgets.QDateEdit()
        self.dateEdit.setDisplayFormat('dd dddd')
        self.dateEdit.setMinimumDateTime(mindate)
        self.dateEdit.setMaximumDateTime(maxdate)
        self.timeEdit = QtWidgets.QTimeEdit()
        self.timeEdit.setDisplayFormat('hh:mm')
        self.titleEdit = QtWidgets.QLineEdit()
        self.peopleEdit = QtWidgets.QLineEdit()

        # attach widgets to layout
        form = QtWidgets.QFormLayout()
        form.addRow('Date', self.dateEdit)
        form.addRow('Time', self.timeEdit)
        form.addRow('Title', self.titleEdit)
        form.addRow('People', self.peopleEdit)

        # create control buttons
        self.okBtn = QtWidgets.QPushButton('OK')
        self.okBtn.clicked.connect(self.on_accept)
        self.cancelBtn = QtWidgets.QPushButton('Cancel')
        self.cancelBtn.clicked.connect(self.reject)

        if not event is None:
            # when edit existing event
            # set data to widgets
            self.setWindowTitle('Edit event of ' + month.date.strftime('%B %Y'))
            self.dateEdit.setDateTime(event.date)
            self.timeEdit.setDateTime(event.date)
            self.titleEdit.setText(event.title)
            self.peopleEdit.setText(event.people)
            self.hash = event.hash # save a hash from last update
            self.okBtn.setEnabled(True) # can save an event
        else:
            # when add new event
            self.setWindowTitle('Add new event to ' + month.date.strftime('%B %Y'))
            self.dateEdit.setDateTime(month.date)
            self.timeEdit.setDateTime(month.date)
            self.hash = None # manually added events have not an update hashsum
            self.okBtn.setEnabled(False) # can't save an event while title is empty

        # disable OK button when title is empty, otherwise enable it
        self.titleEdit.textChanged.connect(lambda text: self.okBtn.setEnabled(bool(text)))

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
        # get data from widgets
        time = self.timeEdit.dateTime().toPyDateTime()
        date = self.dateEdit.dateTime().toPyDateTime()
        date = datetime(date.year, date.month, date.day) + timedelta(hours=time.hour, minutes=time.minute)
        title = self.titleEdit.text()
        people = self.peopleEdit.text()
        # create result event object
        self.event = Event(date, title, people, self.hash)
        self.accept() # set 'accept' code

    def showEvent(self, event):

        """
        Called when dialog is shown.

        """
        QtWidgets.QDialog.showEvent(self, event)
        # if edit an existing event
        if not event is None:
            # set input focus to people widget
            # generally editing would be used to
            # add or change people on the event
            self.peopleEdit.setFocus(0)



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dialog = EditDialog(Month(datetime(2016, 6, 1)))
    dialog.show()
    sys.exit(app.exec_())
