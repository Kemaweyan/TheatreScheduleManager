#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from PyQt5 import QtWidgets, QtCore, QtGui
from datetime import datetime

from theatre.EditDialog import EditDialog
from theatre.TheatreModel import Event
from theatre.Sync import SyncThread
from theatre.Print import Print

# path where script is located
CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))

# path to default application icon
ICON_DEFAULT = os.sep.join([CURRENT_PATH, 'icons', 'icon.png'])
# path to application icon used when there are updates
ICON_NEW = os.sep.join([CURRENT_PATH, 'icons', 'icon_new.png'])

class ControlButton(QtWidgets.QPushButton):

    """
    Base class for buttons on control panel.

    """
    def __init__(self, icon, parent=None):
        QtWidgets.QWidget.__init__(self, icon, '', parent)
        self.setFlat(True) # buttons should be flat



class ControlLabel(QtWidgets.QLabel):

    """
    A label centered in a space with 150px width.

    """
    def __init__(self, text, parent=None):
        QtWidgets.QLabel.__init__(self, text, parent)
        self.setAlignment(QtCore.Qt.AlignHCenter)

    def sizeHint(self):
        sh = QtWidgets.QLabel.sizeHint(self)
        sh.setWidth(150)
        return sh



class ControlWidget(QtWidgets.QWidget):

    """
    Months selector widget.

    """
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        # create control buttons
        self.prev_btn = ControlButton(QtGui.QIcon.fromTheme('previous'))
        self.next_btn = ControlButton(QtGui.QIcon.fromTheme('next'))

        # create selected month ad year indication labels
        self.month = ControlLabel('')
        self.month.setStyleSheet('font-size: 26px;')
        self.year = ControlLabel('')

        # attach labels to layout
        labelBox = QtWidgets.QVBoxLayout()
        labelBox.addWidget(self.month)
        labelBox.addWidget(self.year)

        # add label layout and buttons to main layout
        mainBox = QtWidgets.QHBoxLayout()
        mainBox.addStretch()
        mainBox.addWidget(self.prev_btn)
        mainBox.addLayout(labelBox)
        mainBox.addWidget(self.next_btn)
        mainBox.addStretch()
        # set layout to the window
        self.setLayout(mainBox)
        # change tab order to make Next button active by default
        self.setTabOrder(self.next_btn, self.prev_btn)

    @property
    def next_clicked(self):

        """
        A signal when Next button has been clicked

        """
        return self.next_btn.clicked

    @property
    def prev_clicked(self):

        """
        A signal when Previous button has been clicked

        """
        return self.prev_btn.clicked

    def set_date(self, date):

        """
        Sets the date on the control widget.

        """
        self.month.setText(date.strftime('%B'))
        self.year.setText(date.strftime('%Y'))


class MenuBar(QtWidgets.QMenuBar):

    """
    Main menu bar of the main window

    """
    def __init__(self, parent=None):
        QtWidgets.QMenuBar.__init__(self, parent)

        # create menus and menuitems
        sheduleMenu = self.addMenu('&Shedule')
        self.load_action = sheduleMenu.addAction(QtGui.QIcon.fromTheme('fileopen'), 'Load')
        self.load_action.setShortcut('Ctrl+L')
        self.load_action.setStatusTip('Load saved shedule')
        self.save_action = sheduleMenu.addAction(QtGui.QIcon.fromTheme('filesave'), 'Save')
        self.save_action.setShortcut('Ctrl+S')
        self.save_action.setStatusTip('Save current shedule')
        self.print_action = sheduleMenu.addAction(QtGui.QIcon.fromTheme('fileprint'), 'Print')
        self.print_action.setShortcut('Ctrl+P')
        self.print_action.setStatusTip('Print current shedule')
        self.clear_action = sheduleMenu.addAction(QtGui.QIcon.fromTheme('edit-delete'), 'Clear')
        self.clear_action.setStatusTip('Clear current shedule')
        sheduleMenu.addSeparator()
        self.quit_action = sheduleMenu.addAction(QtGui.QIcon.fromTheme('exit'), 'Quit')
        self.quit_action.setShortcut('Ctrl+Q')
        self.quit_action.setStatusTip('Quit the program')

        editMenu = self.addMenu('&Edit')
        self.add_action = editMenu.addAction(QtGui.QIcon.fromTheme('add'), 'Add event')
        self.add_action.setShortcut('Ctrl+A')
        self.add_action.setStatusTip('Add an event')
        self.edit_action = editMenu.addAction(QtGui.QIcon.fromTheme('gtk-edit'), 'Edit event')
        self.edit_action.setShortcut('Ctrl+E')
        self.edit_action.setStatusTip('Edit selected event')
        self.delete_action = editMenu.addAction(QtGui.QIcon.fromTheme('edit-delete'), 'Delete event')
        self.delete_action.setShortcut('Ctrl+D')
        self.delete_action.setStatusTip('Delete selected event')
        editMenu.addSeparator()
        self.pref_action = editMenu.addAction(QtGui.QIcon.fromTheme('gtk-preferences'), 'Preferences')
        self.pref_action.setStatusTip('Open preferences window')

        navigateMenu = self.addMenu('&Navigation')
        self.next_action = navigateMenu.addAction(QtGui.QIcon.fromTheme('next'), 'Next month')
        self.next_action.setShortcut('Ctrl+F')
        self.next_action.setStatusTip('Open next month')
        self.prev_action = navigateMenu.addAction(QtGui.QIcon.fromTheme('previous'), 'Previous month')
        self.prev_action.setShortcut('Ctrl+B')
        self.prev_action.setStatusTip('Open previous month')
        self.actual_action = navigateMenu.addAction(QtGui.QIcon.fromTheme('go-home'), 'Current month')
        self.actual_action.setShortcut('Ctrl+H')
        self.actual_action.setStatusTip('Open currect month')

        syncMenu = self.addMenu('&Sync')
        self.sync_all_action = syncMenu.addAction(QtGui.QIcon.fromTheme('reload'), 'Sync all')
        self.sync_all_action.setStatusTip('Sync all shedules')



class TableContextMenu(QtWidgets.QMenu):

    """
    Context menu of the table view.

    """
    def __init__(self, parent=None):
        QtWidgets.QMenu.__init__(self, parent)

        # create actions
        self.add_action = self.addAction(QtGui.QIcon.fromTheme('add'), "Add event")
        self.edit_action = self.addAction(QtGui.QIcon.fromTheme('gtk-edit'), "Edit event")
        self.delete_action = self.addAction(QtGui.QIcon.fromTheme('edit-delete'), "Delete event")



class SheduleTableView(QtWidgets.QTableView):

    """
    A table containing a shedule of selected month.

    """
    # a signal emitted when Enter key has been pressed
    enter_pressed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QtWidgets.QTableView.__init__(self, parent)
        # select a whole row only
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        # select only one row at a time
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.verticalHeader().hide() # no vertical header
        # fixed size of horizontal header items
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        # initially selected nothing
        self.selected_event = None
        self.selected_row = None
        self.menu = TableContextMenu()

    def resizeEvent(self, event):

        """
        Called when TableView is resized.
        Resizes columns to fill a whole width.

        """
        size = event.size()
        # widths of columns 0, 1 and 3 are fixed
        self.setColumnWidth(0, 60)
        self.setColumnWidth(1, 70)
        self.setColumnWidth(3, 70)
        # column 2 fills the rest of width
        self.setColumnWidth(2, size.width() - 200)

    def setModel(self, model):

        """
        Sets a model of selected month's shedule.

        """
        QtWidgets.QTableView.setModel(self, model)
        self.selectionModel().selectionChanged.connect(self.selection_changed)
        # clearselected items
        self.selected_event = None
        self.selected_row = None
        if model.date == datetime(datetime.today().year, datetime.today().month, 1):
            # if current month has been selected
            # select nearest event and scrool to it
            row = 0 # current row is 0
            for event in model:
                if event.date >= datetime.now():
                    # if next event will be in the future
                    self.selectRow(row) # select current event
                    self.scrollTo(self.selectedIndexes()[0])
                    break
                row += 1 # go to next row

    @QtCore.pyqtSlot('QItemSelection', 'QItemSelection')
    def selection_changed(self, selected, deselected):

        """
        Called when user selected an event.
        Sets selected event and row number.

        """
        cells = selected.indexes() # get selected cells
        # read data from selected cells
        date = cells[0].data(QtCore.Qt.UserRole + 1)
        title = cells[2].data()
        hashsum = cells[2].data(QtCore.Qt.UserRole + 1)
        people = cells[3].data()
        # create an event object
        self.selected_event = Event(date, title, people, hashsum)
        self.selected_row = cells[0].row() # get selected row number

    def mousePressEvent(self, event):

        """
        Called when user pressed a mouse button.
        Shows context menu on right-click.

        """
        QtWidgets.QTableView.mousePressEvent(self, event)
        if event.button() == QtCore.Qt.RightButton:
            self.menu.exec_(QtGui.QCursor.pos())

    def keyPressEvent(self, event):

        """
        Called when user pressed a keyboard key.

        """
        QtWidgets.QTableView.keyPressEvent(self, event)
        if event.key() == QtCore.Qt.Key_Enter or event.key() == QtCore.Qt.Key_Return:
            self.enter_pressed.emit() # emit Enter pressed signal




class MainWindow(QtWidgets.QMainWindow):

    """
    The application main window.

    """
    # a signal emitted when visibility of the window changes
    visible_signal = QtCore.pyqtSignal(bool)

    def __init__(self, shedule, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        self.resize(600, 500)
        self.setWindowTitle("Theatre Shedule Manager")
        self.setWindowIcon(QtGui.QIcon(ICON_DEFAULT))
        self.statusBar() # create statusbar

        self.shedule = shedule
        self.thread = None # sinchronization thread

        # create menu bar and connect signals
        self.menubar = MenuBar(self)
        self.setMenuBar(self.menubar)
        self.menubar.load_action.triggered.connect(self.on_load_clicked)
        self.menubar.save_action.triggered.connect(self.on_save_clicked)
        self.menubar.clear_action.triggered.connect(self.on_clear_clicked)
        self.menubar.print_action.triggered.connect(self.on_print_clicked)
        self.menubar.add_action.triggered.connect(self.on_add_clicked)
        self.menubar.edit_action.triggered.connect(self.on_edit_clicked)
        self.menubar.delete_action.triggered.connect(self.on_delete_clicked)
        self.menubar.next_action.triggered.connect(self.on_next_clicked)
        self.menubar.prev_action.triggered.connect(self.on_prev_clicked)
        self.menubar.actual_action.triggered.connect(self.set_actual_month)

        # create control widget and connect signals
        self.control_widget = ControlWidget()
        self.control_widget.next_clicked.connect(self.on_next_clicked)
        self.control_widget.prev_clicked.connect(self.on_prev_clicked)
        # locate control widget on Top Dock Widget
        dock_widget = QtWidgets.QDockWidget(self)
        dock_widget.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        dock_widget.setWidget(self.control_widget)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, dock_widget)

        # create table view
        self.table = SheduleTableView(self)
        # edit event on double click and enter
        self.table.doubleClicked.connect(lambda index: self.on_edit_clicked())
        self.table.enter_pressed.connect(self.on_edit_clicked)
        self.setCentralWidget(self.table) # use table as central widget
        # connect table context menu actions
        self.table.menu.add_action.triggered.connect(self.on_add_clicked)
        self.table.menu.edit_action.triggered.connect(self.on_edit_clicked)
        self.table.menu.delete_action.triggered.connect(self.on_delete_clicked)

        self.set_actual_month() # select current month

    def closeEvent(self, event):

        """
        Called when the window was closed.

        """
        self.hide() # hide the window
        event.ignore() # do not destroy the window

    def hideEvent(self, event):

        """
        Called when the window was hidden.

        """
        self.visible_signal.emit(False)

    def showEvent(self, event):

        """
        Called when the window was shown.

        """
        self.visible_signal.emit(True)

    @QtCore.pyqtSlot()
    def set_actual_month(self):

        """
        Sets current month to the table.

        """
        # get a model from the shedule
        model = self.shedule.get_actual()
        # set the model
        self.table.setModel(model)
        # change a date of control widget
        self.control_widget.set_date(model.date)

    @QtCore.pyqtSlot()
    def on_next_clicked(self):

        """
        Sets the next month to the table.

        """
        # get a model from the shedule
        model = self.shedule.get_next()
        # set the model
        self.table.setModel(model)
        # change a date of control widget
        self.control_widget.set_date(model.date)

    @QtCore.pyqtSlot()
    def on_prev_clicked(self):

        """
        Sets the previous month to the table.

        """
        # get a model from the shedule
        model = self.shedule.get_previous()
        # set the model
        self.table.setModel(model)
        # change a date of control widget
        self.control_widget.set_date(model.date)

    # signals from main menu to tray icon

    @property
    def quit_signal(self):
        return self.menubar.quit_action.triggered

    @property
    def sync_all_signal(self):
        return self.menubar.sync_all_action.triggered

    @property
    def pref_signal(self):
        return self.menubar.pref_action.triggered

    @QtCore.pyqtSlot()
    def on_add_clicked(self):

        """
        Adds a new event to the month.

        """
        model = self.table.model()
        # create EditDialog without event
        dialog = EditDialog(model, parent=self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            model.add(dialog.event)

    @QtCore.pyqtSlot()
    def on_edit_clicked(self):

        """
        Edits selected event.

        """
        model = self.table.model()
        # do nothing if there is no selected event
        if self.table.selected_event is None:
            return
        # create EditDialog with selected event
        dialog = EditDialog(model, self.table.selected_event, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            model.replace(self.table.selected_row, dialog.event)
    
    @QtCore.pyqtSlot()
    def on_delete_clicked(self):

        """
        Deletes selected event.

        """
        model = self.table.model()
        # do nothing if there is no selected event
        if self.table.selected_row is None:
            return
        # ask a confirmation
        msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, 'Delete confirmation', 'Are you sure to delete this event?', 
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, self)
        answer = msg.exec_()
        if answer == QtWidgets.QMessageBox.Yes:
            model.delete(self.table.selected_row)

    @QtCore.pyqtSlot()
    def on_load_clicked(self):

        """
        Loads saved model data.

        """
        model = self.table.model()
        if model.changed: # if model has been changed
            # ask a confirmation to reload data
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, 'Reload confirmation', 'Data was changed. Do you really want to load old data?', 
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, self)
            if msg.exec_() == QtWidgets.QMessageBox.No:
                return
        model.clear() # remove all events
        model.load() # load events
    
    @QtCore.pyqtSlot()
    def on_save_clicked(self):

        """
        Saves model data.

        """
        model = self.table.model()
        model.save()

    @QtCore.pyqtSlot()
    def on_clear_clicked(self):

        """
        Removes all events.

        """
        model = self.table.model()
        # ask a confirmation
        msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, 'Clear confirmation', 'Are you sure to remove all events?', 
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, self)
        if msg_box.exec_() == QtWidgets.QMessageBox.Yes:
            model.clear()

    @QtCore.pyqtSlot()
    def on_print_clicked(self):

        """
        Prints a shedule of the month.

        """
        # create Print object
        printing = Print(self.table.model())
        try:
            printing.print_month() # print shedule
        except AssertionError as e:
            # show message if an error has occurred
            msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical, 'Print error', str(e), QtWidgets.QMessageBox.Ok, self)
            msg_box.show()
