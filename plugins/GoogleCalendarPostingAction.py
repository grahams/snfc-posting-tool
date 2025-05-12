from datetime import datetime
import os
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from BasePostingAction import BasePostingAction

SCOPES = ['https://www.googleapis.com/auth/calendar.events.owned']

class GoogleCalendarPostingAction(BasePostingAction):
    pluginName = "Google Calendar"
    configSection = "googleCalendar"
    config = None

    def parse_time(self, t):
        p = re.search('^([0-1]?)([0-9])(:?)([0-9]{0,2})([aAPp]?.?)', t)

        if p is None:
            raise ValueError("Invalid time format")

        tens = p.group(1)
        hour = p.group(2)
        minute = p.group(4)
        ampm = p.group(5)

        if tens == '':
            hour = '0' + hour
        
        if minute == '':
            minute = '00'
        
        if ampm.startswith('p') or ampm.startswith('P'):
            hour = int(hour) + 12

        return int(hour), int(minute)

    def execute(self, config, nl):
        self.config = config

        calendarId = self.read_config_value('calendarId')

        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
                # Save the credentials for the next run

                with open("token.json", "w") as token:
                    token.write(creds.to_json())

        try:
            service = build("calendar", "v3", credentials=creds)

            dateString = nl.get_next_sunday().strftime("%FT")

            (hours, minutes) = self.parse_time(nl.normalize_time(nl.showTime))

            start_time = "%s%.2d:%.2d:00.000" % (dateString, hours, minutes)
            end_time = "%s%.2d:%.2d:00.000" % (dateString, hours + 3, minutes)

            # Convert the event to Google Calendar format
            google_event = {
                'summary': nl.generate_subject(),
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'America/New_York',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'America/New_York',
                },
                'description': nl.generate_HTML(),
            }

            

            # Post the event to Google Calendar
            event = service.events().insert(calendarId=calendarId, body=google_event).execute()
            url = event.get('htmlLink')
            return(f"Posted to the <a href='{url}'>Calendar</a><br />")




        except(HttpError):
            return("Error posting to Google Calendar<br />")