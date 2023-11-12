from Newsletter import Newsletter
from BasePostingAction import BasePostingAction

try:
  from xml.etree import ElementTree # for Python 2.5 users
except ImportError:
  from elementtree import ElementTree

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run_flow
from oauth2client.client import flow_from_clientsecrets
import httplib2

import gdata.calendar.data
import gdata.calendar.client

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
        calendarId = self.readConfigValue('calendarId')
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
        hours += 12 

        start_time = "%s%.2d:%.2d:00.000" % (dateString, hours, minutes)
        end_time = "%s%.2d:%.2d:00.000" % (dateString, hours + 3, minutes)

        nlText = str(nl.generatePlainText())

        event = {
          'summary': nl.film + titleText,
          'location': nl.location,
          'description': nlText,
          'start': {
            'dateTime': start_time,
            'timeZone': 'America/New_York',
          },
          'end': {
            'dateTime': end_time,
            'timeZone': 'America/New_York',
          },
        }

        scope = 'https://www.googleapis.com/auth/calendar'
        flow = flow_from_clientsecrets('/usr/share/wordpress/tool/boston/.client_secret.json', scope=scope)

        storage = Storage('/usr/share/wordpress/tool/boston/credentials.dat')
        credentials = storage.get()

        class fakeargparse(object):  # fake argparse.Namespace
            noauth_local_webserver = True
            logging_level = "ERROR"
        flags = fakeargparse()

        if credentials is None or credentials.invalid:
            credentials = run_flow(flow, storage, flags)

        http = httplib2.Http(ca_certs="/etc/ssl/certs/ca-certificates.crt")
        http.add_certificate
        http = credentials.authorize(http)
        service = build('calendar', 'v3', http=http)

        new_event = service.events().insert(calendarId=calendarId, body=event).execute()

        print 'Posted to <a href="' + str(new_event.get('htmlLink')) + '">Google Calendar</a><br />'

