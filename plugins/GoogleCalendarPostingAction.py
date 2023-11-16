from datetime import datetime
import os

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

    from datetime import datetime

    def parse_time(self, t):
        if 'p' in t:
            t = t.replace('p', '')
            format = '%I%M' if ':' not in t else '%I:%M'
            dt = datetime.strptime(t, format)
            return (dt.hour + 12) % 24, dt.minute
        else:
            format = '%H%M' if ':' not in t else '%H:%M'
            dt = datetime.strptime(t, format)
            return dt.hour, dt.minute

    def execute(self, config, nl):
        """Shows basic usage of the Google Calendar API.
        Prints the start and name of the next 10 events on the user's calendar.
        """
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

            dateString = nl.nextSunday.strftime("%FT")

            (hours, minutes) = self.parse_time(nl.showTime)

            if hours < 12:
                hours += 12

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
                'description': nl.generate_plain_text(),
            }

            # Post the event to Google Calendar
            event = service.events().insert(calendarId='primary', body=google_event).execute()
            url = event.get('htmlLink')
            return(f"Posted to the <a href='{url}'>Calendar</a><br />")




        except(HttpError):
            return("Error posting to Google Calendar<br />")