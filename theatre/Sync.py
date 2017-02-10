#!/usr/bin/env python3

from http import client
from http.client import HTTPConnection
from PyQt5 import QtCore
from datetime import datetime
import re
import hashlib

from easyhtml.parser import DOMParser
from theatre.TheatreModel import Event

# host for synchronization
HOST = 'www.operetta.kharkiv.ua'

# network error class
class NetworkError(Exception): pass

class Downloader:

    """
    Gets data from the server.

    """
    def __init__(self, url):
        try:
            # connect to host and send request
            connection = HTTPConnection(HOST)
            connection.request('GET', url)
        except:
            # a connection error has occurred
            raise NetworkError('Network or server is unavailable')
        try:
            # get server response
            self.response = connection.getresponse()
        except:
            # a download error has occurred
            raise NetworkError('Could not get server response')

    @property
    def status(self):

        """
        HTTP response status

        """
        return self.response.status

    @property
    def reason(self):

        """
        HTTP response reason

        """
        return self.response.reason

    @property
    def data(self):

        """
        HTTP response data

        """
        return self.response.read()



#class Parser:
#
#    """
#    Parses downloaded data (html page).
#
#    """
#    # a pattern for each event in the shedule on the web page
#    event_re = re.compile('<article class="post">.+?<span.+?(?:</strong>&nbsp;)?(\d{2})(?:</strong>)?:(\d{2})(?:<br />)?</span>.+?<strong>(\d{1,2})(?:<br />)?</strong>.+?#<strong>(\w+)</strong></span></p>.+?(?:(?:title="(.+?)")|(?:<span style="color: #d1a858;">([\w\s\d]+)[^<>]*?</span>)).+?</article>', re.S)
#
#    # a pattern to search a link to the next page
#    forward_re = re.compile('start=(\d+)"[^<>]+>Вперёд</a>', re.S)
#
#    # a dictionary for translating months' names to numbers
#    month_names = { 'января':   1,
#                    'февраля':  2,
#                    'марта':    3,
#                    'апреля':   4,
#                    'мая':      5,
#                    'июня':     6,
#                    'июля':     7,
#                    'августа':  8,
#                    'сентября': 9,
#                    'октября': 10,
#                    'ноября':  11,
#                    'декабря': 12   }
#
#    def __init__(self, data):
#        self.data = data
#        self.forward = None
#
#    def parse(self):
#
#        """
#        Parses the shedule table data
#        and returns found data for events.
#
#        """
#        # find all events
#        matches = self.event_re.findall(self.data)
#        raw_events = [] # a list of events data
#        for match in matches:
#            try:
#                hours = int(match[0])
#                minutes = int(match[1])
#                day = int(match[2])
#                month_name = match[3]
#                month = self.month_names[month_name.lower()]
#                year = datetime.now().year
#                # get title from a link or from a raw text
#                title = match[4] if match[4] else match[5]
#
#                # if the month in the future has
#                # a bigger number than current month
#                if month < datetime.now().month:
#                    year += 1 # it belongs to the next year
#
#                # create a key for a dictionary
#                month_id = '{0}{1:0>2}'.format(year, month)
#                date = datetime(year, month, day, hours, minutes)
#
#                # add data to the list
#                raw_events.append((month_id, date, title))
#
#                # get the next page
#                forward = self.forward_re.search(self.data)
#                if forward:
#                    self.forward = int(forward.group(1))
#            except:
#                pass
#        return raw_events



class Parser:

    """
    Parses downloaded data (html page).

    """
    # a dictionary for translating months' names to numbers
    month_names = { 'января':   1,
                    'февраля':  2,
                    'марта':    3,
                    'апреля':   4,
                    'мая':      5,
                    'июня':     6,
                    'июля':     7,
                    'августа':  8,
                    'сентября': 9,
                    'октября': 10,
                    'ноября':  11,
                    'декабря': 12   }

    def __init__(self, data):
        # create HTML parser
        parser = DOMParser()
        parser.feed(data)
        # get DOM of the page
        self.document = parser.get_dom()
        # the next page is not yet known
        self.forward = None

    def parse(self):

        """
        Parses the shedule table data
        and returns found data for events.

        """
        # a list of events data
        raw_events = []
        # there is <article class="post"> object for each event
        for article in self.document.article('class=post'):
            # get all <span> objects in the <article>
            spans = article.span
            try:
                # the first <span> contains a weekday
                # and a time of the event separated by spaces
                time = re.split('\s+', str(spans[0]))[1]
                # the second <span> contains a day
                day = str(spans[1])
                # the third <span> contains a name of a month
                # written with russian letters in upper case
                # get its number from the dictionary month_names
                month = self.month_names[str(spans[2]).lower()]

                # assume that a year of the event
                # is the current year
                year = datetime.now().year
                # if a month of the event has
                # lesser number than the current month
                if month < datetime.now().month:
                    year += 1 # it belongs to the next year

                # month_id is a string YYYYMM
                month_id = '{0}{1:0>2}'.format(year, month)
                # create a datetime object from the string YYYY.MM.DD HH:MM
                date = datetime.strptime("{0}.{1:0>2}.{2:0>2} {3}".format(year, month, day, time), "%Y.%m.%d %H:%M")

                try:
                    # get all <p> objects
                    paragraphs = article.p
                    # a title of the event is a 'title' attribute
                    # of an <a> object in the second <p> object
                    #links = paragraphs.get_element(1).a
                    #title = links.get_element(0).get_attr('title')
                    links = paragraphs[2].a
                    title = str(links[0])
                    # if the link text is empty
                    if not title:
                        raise Exception
                except:
                    # if structure differs then an error has occured
                    # in this case use seventh <span> object as a title
                    title = str(spans[7])

                # add an event data to the list after
                # removing all space symbols around the title string
                raw_events.append((month_id, date, title.strip(' \n\t\xA0')))
            except:
                # if there was something wrong - skip this <article>
                continue

        # after processing all <article> objects
        # get a link to the next page
        try:
            # get a <div class="pager"> objects
            pagers = self.document.div('class=pager')
            # it should be only one so if it exists
            # get it from the list with index 0
            pager = pagers[0]
            # get a link to the next page with title "Вперёд"
            links = pager.get_children('title=Вперёд')
            # get 'href' attribute of the first link
            url = links[0].get_attr('href')
            # 'href' is separated by = and the second part
            # is a number of starting event on the next page
            next_id = url.split('=')[1]
            # save it in 'forward' variable
            self.forward = int(next_id)
        except:
            # if there was something wrong -
            # assume that there is no next page
            self.forward = None

        # return a list of events data
        return raw_events



class SyncThread(QtCore.QThread):

    """
    Runs synchronization in separate thread.

    """
    complete = QtCore.pyqtSignal() # sync OK
    failure = QtCore.pyqtSignal(str) # sync error

    url = '/rus/?start={}'

    def __init__(self):
        self.events = {} # a dictionary events data
        QtCore.QThread.__init__(self)

    def run(self):
        start_msg = 0
        while True:
            try:
                url = self.url.format(start_msg)
                downloader = Downloader(url)
            except NetworkError as e:
                # a download error has occurred
                self.failure.emit(str(e))
                return
            else:
                # downloading OK
                if downloader.status == client.OK:
                    data = downloader.data # get data
                    parser = Parser(data.decode('utf-8'))
                    # parse events
                    raw_events = parser.parse()

                    # create an Event object for each item
                    for raw_event in raw_events:
                        month_id = raw_event[0]
                        raw_str = raw_event[1].strftime('%Y.%m.%d %H:%M') + raw_event[2]
                        m = hashlib.md5(raw_str.encode())
                        hashsum = m.digest()
                        event = Event(raw_event[1], raw_event[2], hashsum=hashsum)
                        # add event to existing list
                        if month_id in self.events:
                            self.events[month_id].append(event)
                        else: # or create a new list
                            self.events[month_id] = [event]

                    # # last page of shedule
                    if parser.forward is None:
                        # sync OK
                        self.complete.emit()
                        return

                    start_msg = parser.forward
                else:
                    # a HTTP error has occurred
                    self.failure.emit(downloader.reason)
                    return
