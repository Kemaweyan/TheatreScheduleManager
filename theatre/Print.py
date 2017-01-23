#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets, QtGui, QtPrintSupport
from datetime import datetime

def align_left(text, fm, indent, height, x_offset=0, y_offset=0):

    """
    Aligns text to left.

    """
    textRect = fm.boundingRect(text) # a rect around the text
    x = indent # x coordinate is an indent
    # y coordinate is a half of free vertical space + font ascent
    y = (height - textRect.height()) / 2 + fm.ascent()
    # add text offsets to coordinates
    return QtCore.QPointF(x + x_offset, y + y_offset)

def align_center(text, fm, width, height, x_offset=0, y_offset=0):

    """
    Aligns text to center.

    """
    textRect = fm.boundingRect(text) # a rect around the text
    # x coordinate is a half of free horizontal space
    x = (width - textRect.width()) / 2
    # y coordinate is a half of free vertical space + font ascent
    y = (height - textRect.height()) / 2 + fm.ascent()
    # add text offsets to coordinates
    return QtCore.QPointF(x + x_offset, y + y_offset)

class Print():

    """
    Prints shedule of a month.

    """
    header_height = 40.0 # a height of a header (month + year)
    line_width = 1.001 # a width of grid lines

    def __init__(self, month, parent=None):
        self.month = month
        self.parent = parent
        self.painter = QtGui.QPainter()
        self.pageRect = None
        self.row_height = 0

    def print_month(self):

        """
        Prints a month's shedule

        """
        # there should be at least one event
        assert self.month.rowCount() > 0, "Shedule is empty. Nothing to print."
        # open print dialog
        dialog = QtPrintSupport.QPrintDialog(self.parent)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # get printer
            printer = dialog.printer()
            # error if printing impossible
            assert self.painter.begin(printer), "Can't open printer."
            self.pageRect = printer.pageRect() # get page rect
            # calculate a height of each row, maximum height is 50
            self.row_height = min((self.pageRect.height() - self.header_height) / self.month.rowCount(), 50.0)
            self.table_height = self.row_height * self.month.rowCount() # a height of the shedule table
            pen = QtGui.QPen(1) # solid pen
            pen.setWidthF(self.line_width)
            self.painter.setPen(pen)
            self.draw_header() # print a header
            self.draw_grid() # print a grid
            self.draw_events() # print events
            self.painter.end() # done

    def draw_header(self):

        """
        Draws a page header that consists of
        a name of the month and a year.

        """
        # text to print
        text = self.month.date.strftime('%B %Y').upper()
        # select a font
        font = QtGui.QFont('Times New Roman', 16)
        fm = QtGui.QFontMetrics(font)
        self.painter.setFont(font)
        # print center-aligned text
        self.painter.drawText(align_center(text, fm, self.pageRect.width(), self.header_height), text)

    def draw_grid(self):

        """
        Draws a grid of the table.

        """
        # print outer lines
        self.painter.drawRect(QtCore.QRectF(0.0, self.header_height, self.pageRect.width(), self.table_height))
        # print vertical lines (column separators)
        self.painter.drawLine(QtCore.QLineF(70.0, self.header_height, 70.0, self.header_height + self.table_height))
        self.painter.drawLine(QtCore.QLineF(140.0, self.header_height, 140.0, self.header_height + self.table_height))
        self.painter.drawLine(QtCore.QLineF(self.pageRect.width() - 70.0, self.header_height, self.pageRect.width() - 70.0, self.header_height + self.table_height))
        # draw horizontal lines between all days
        # do not draw lines between evens at the same day
        it = iter(self.month) # get month's iterator
        prev_event = next(it) # save first event as previous
        # and begin from the second event to pre-last
        # do not draw a line after the last event
        for y in range(1, self.month.rowCount()):
            event = next(it) # get event
            if prev_event.date.day == event.date.day:
                # skip an event if its date is the same
                # as in the previous event
                continue
            prev_event = event # save the event as previous
            # calculate y coordinate above a row with the event
            y_pos = y * self.row_height + self.header_height
            # draw a line
            self.painter.drawLine(QtCore.QLineF(0.0, y_pos, self.pageRect.width(), y_pos))

    def draw_events(self):

        """
        Draws a data of events.

        """
        # select a font
        font = QtGui.QFont('Times New Roman', 14)
        fm = QtGui.QFontMetrics(font)
        self.painter.setFont(font)
        # start from the bottom of the header
        y_pos = self.header_height
        prev_event = None # initially there is no previous event
        for event in self.month:
            # only for new days
            if prev_event is None or prev_event.date.day != event.date.day:
                # print a date
                prev_event = event
                date = event.date.strftime('%d %a')
                self.painter.drawText(align_left(date, fm, 7.0, self.row_height, y_offset=y_pos), date)
            time = event.date.strftime('%H:%M') # time format
            # print a time center-aligned
            self.painter.drawText(align_center(time, fm, 70.0, self.row_height, x_offset=70.0, y_offset=y_pos), time)
            # print a title left-aligned with 15.0 indent
            self.painter.drawText(align_left(event.title, fm, 15.0, self.row_height, x_offset=140.0, y_offset=y_pos), event.title)
            # print people center-aligned
            self.painter.drawText(align_center(event.people, fm, 70.0, self.row_height, x_offset=self.pageRect.width() - 70.0, y_offset=y_pos), event.people)
            y_pos += self.row_height # go to the next row
