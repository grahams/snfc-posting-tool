from Newsletter import Newsletter
from BasePostingAction import BasePostingAction

try:
  from xml.etree import ElementTree # for Python 2.5 users
except ImportError:
  from elementtree import ElementTree
import gdata.calendar.service
import gdata.service
import atom.service
import gdata.calendar
import atom
import getopt
import sys
import string
import time

from mx.DateTime import *

class GoogleCalendarPostingAction(BasePostingAction):
    pluginName = "Google Calendar"
    configSection = 'googleCalendar'
    config = None

    def execute(self, config, nl):
        self.config = config
        email = self.readConfigValue('email')
        password = self.readConfigValue('password')
        path = self.readConfigValue('path')
        titleText = self.readConfigValue('titleText')

        dateString = nl.nextSunday.strftime("%FT")

        if(nl.showTime.find(":") > -1):
            times = nl.showTime.split(":")
            hours = int(times[0])
            minutes = int(times[1].strip("aApPmM ."))
        else:
            hours = int(nl.showTime.strip("aApPmM ."))
            minutes = 0;

        # adjust for 24 hour clock and DST if neccessary
        hours += 12 + 5 - nl.nextSunday.dst

        start_time = "%s%.2d:%.2d:00.000Z" % (dateString, hours, minutes)
        end_time = "%s%.2d:%.2d:00.000Z" % (dateString, hours + 4, minutes)

        nlText = str(nl.generatePlainText())

        event = gdata.calendar.CalendarEventEntry()
        event.title = atom.Title(text=nl.film + titleText)
        event.content = atom.Content(text=nlText)
        event.where.append(gdata.calendar.Where(value_string=nl.location))

        event.when.append(gdata.calendar.When(start_time=start_time, end_time=end_time))

        calendar_service = gdata.calendar.service.CalendarService()
        calendar_service.email = email
        calendar_service.password = password
        calendar_service.source = 'Google-Calendar_Python_Sample-1.0'
        calendar_service.ProgrammaticLogin()

        new_event = calendar_service.InsertEvent(event, path)

        print 'Posted to <a href="' + new_event.GetHtmlLink().href + '">Google Calendar</a><br />'
