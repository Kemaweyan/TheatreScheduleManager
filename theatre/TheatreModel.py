#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui
from datetime import datetime
import shelve

class Storage:

    """
    Reads and writes data using shelve module.

    """
    def __init__(self, filename):
        self.db = shelve.open(filename)

    def read(self, key):
        return self.db[key]

    def write(self, key, data):
        self.db[key] = data

    def close(self):
        self.db.close()



class Event:

    """
    A theatre event (performance, concert).

    """
    def __init__(self, date, title, people=None, hashsum=None):
        self.date = date
        self.title = title
        self.people = people
        self.hash = hashsum

    def row(self):

        """
        Returns a row for QStandardItemModel
        using Event elements.

        """
        date_item = QtGui.QStandardItem(self.date.strftime('%d %a'))
        date_item.setData(self.date) # date field contains a datetime object of the event
        time_item = QtGui.QStandardItem(self.date.strftime('%H:%M'))
        time_item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        title_item = QtGui.QStandardItem(self.title)
        title_item.setData(self.hash) # title field contains a hashsum of the event
        people_item = QtGui.QStandardItem(self.people)
        people_item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        row = (date_item, time_item, title_item, people_item)
        # forbid editting of all fields
        for item in row:
            item.setEditable(False)
        return row


class SortProxyModel(QtCore.QSortFilterProxyModel):

    """
    Sorts events in the model.
    Is iterable.

    """
    def __init__(self, model, parent=None):
        QtCore.QSortFilterProxyModel.__init__(self, parent)

        self.setSortRole(QtCore.Qt.UserRole + 1) # sort by datetime object
        self.setSourceModel(model)
        self.sort(0)

    def lessThan(self, leftIndex, rightIndex):

        """
        Compares values of datetime objects
        in date fields of each row.

        """
        model = self.sourceModel()
        return model.data(leftIndex, QtCore.Qt.UserRole + 1) < model.data(rightIndex, QtCore.Qt.UserRole + 1)

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):

        """
        Each iteration returns an Event object
        in sorted order.

        """
        if self._index >= self.rowCount():
            raise StopIteration
        date = self.data(self.index(self._index, 0), QtCore.Qt.UserRole + 1)
        title = self.data(self.index(self._index, 2))
        people = self.data(self.index(self._index, 3))
        self._index += 1
        return Event(date, title, people)

    def __getattr__(self, name):

        """
        Redirects unknown attributes requests to source model.

        """
        return getattr(self.sourceModel(), name)

    def add(self, event):

        """
        Adds an event to the model. Affects source model.
        Re-sorts events.

        """
        self.appendRow(event.row())
        self.sourceModel().changed = True
        self.sort(0)

    def delete(self, row):

        """
        Deletes an event from the model. Affects source model.

        """
        self.removeRow(row)
        self.sourceModel().changed = True

    def replace(self, row, event):

        """
        Replaces existing event from the model
        and adds a new event. Affects source model.
        Re-sorts events.

        """
        self.delete(row)
        self.add(event)



class Month(QtGui.QStandardItemModel):

    """
    A model used by QTableView. Contains a collection of events.
    Is iterable.

    """
    def __init__(self, date, storage):
        QtGui.QStandardItemModel.__init__(self)
        self.storage = storage
        self.setHorizontalHeaderLabels(['Date', 'Time', 'Title', 'Who'])
        self.key = date.strftime('%Y%m')
        self.date = datetime(date.year, date.month, 1)
        self.changed = False
        # signal will be emitted when the model is changed manually 
        self.dataChanged.connect(self.on_changed)
        try:
            self.load() # try load data
        except:
            pass

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):

        """
        Each iteration returns an Event object
        in random order.

        """
        if self._index >= self.rowCount():
            raise StopIteration
        date = self.data(self.index(self._index, 0), QtCore.Qt.UserRole + 1)
        title = self.data(self.index(self._index, 2))
        hashsum = self.data(self.index(self._index, 2), QtCore.Qt.UserRole + 1)
        people = self.data(self.index(self._index, 3))
        self._index += 1
        return Event(date, title, people, hashsum)

    def load(self):

        """
        Loads model data from the storage.

        """
        events = self.storage.read(self.key)
        for event in events:
            self.appendRow(event.row())
        self.changed = False

    def save(self):

        """
        Saves model data to the storage if data has been changed.

        """
        if not self.changed:
            return
        events = []
        for event in self:
            events.append(event)
        self.storage.write(self.key, events)
        self.changed = False

    def clear(self):

        """
        Removes all events from the model.

        """
        QtGui.QStandardItemModel.clear(self)
        self.setHorizontalHeaderLabels(['Date', 'Time', 'Title', 'Who'])
        self.changed = True

    @QtCore.pyqtSlot('QModelIndex', 'QModelIndex')
    def on_changed(self, topLeft, bottomRight):

        """
        Called when the model has been changed manually.
        self.changed flag means that the model needs saving.

        """
        self.changed = True

    def search_event(self, search_event):

        """
        Searches the event by its date.

        """
        for event in self:
            if event.date == search_event.date:
                return (event, self._index - 1)
        return (None, None)

    def update(self, event_list):

        """
        Updates the model using raw data from the thetre website.

        """
        changes = []
        # check for new events in the update
        for new_event in event_list:
            # skip events in the past
            if new_event.date < datetime.now():
                continue
            event, row = self.search_event(new_event)
            if event is None: # the event is new
                self.appendRow(new_event.row())
                changes.append('Added:   {} {}'.format(new_event.date.strftime('%d %a %H:%M'), new_event.title))
            elif event.hash != new_event.hash: # the event has beed changed
                self.removeRow(row)
                new_event.people = event.people
                self.appendRow(new_event.row())
                changes.append('Changed: {} {}\n{:>21}'.format(event.date.strftime('%d %a %H:%M'), event.title, new_event.title))

        # search removed events
        for event in self:
            # skip events in the past
            if event.date < datetime.now():
                continue
            for new_event in event_list:
                # break if the event has been added manually (hashsum is None)
                # or it exists in update data
                if event.hash is None or event.hash == new_event.hash:
                    break
            else: # nothing matched, break has not been executed
                # remove event, self._index has been incremented
                # by 'next' method before it returned an Event
                self.removeRow(self._index - 1)
                changes.append('Removed: {} {}'.format(event.date.strftime('%d %a %H:%M'), event.title))

        if changes:
            self.changed = True

        return changes


class Shedule:

    """
    Contains a collectin of models for all months.

    """
    def __init__(self, filename=None):
        self.current_year = datetime.today().year
        self.current_month = datetime.today().month
        self.storage = Storage(filename)
        self.cache = {} # a cache to store loaded months

    def close(self):
        self.storage.close()

    def get_month(self, date=None, key=None):

        """
        Returns a model of requested month

        """
        if not key:
            key = date.strftime('%Y%m')
        else:
            date = datetime.strptime(key, '%Y%m')
        if key not in self.cache: # if there is not requested model in the cache
            # get it from the storage and put in the cache
            self.cache[key] = SortProxyModel(Month(date, self.storage))
        return self.cache[key] # get from the cache

    def get_actual(self):

        """
        Returns a model of the current month

        """
        return self.get_month(datetime.now())

    def get_next(self):

        """
        Returns the next month's model.

        """
        self.current_month += 1 # next month
        # if the next month is 13
        if self.current_month > 12:
            # then now is December
            # and the next month is January
            self.current_month = 1
            # of the next year
            self.current_year += 1
        return self.get_month(datetime(self.current_year, self.current_month, 1))

    def get_previous(self):

        """
        Returns the previous month's model.

        """
        self.current_month -= 1 # previous month
        # if the previous month is 0
        if self.current_month < 1:
            # then now is January
            # and the previous month is December
            self.current_month = 12
            # of the previous year
            self.current_year -= 1
        return self.get_month(datetime(self.current_year, self.current_month, 1))

    def is_changed(self):

        """
        Checks for changed models in the shedule

        """
        for key, month in self.cache.items():
            if month.changed:
                return True
        return False

    def save_cache(self):

        """
        Saves models in the cache to the storage.

        """
        for key, month in self.cache.items():
            month.save()
