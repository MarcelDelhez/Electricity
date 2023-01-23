from __future__ import print_function

import datetime
import os.path

import googlemaps
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
Depart = '... Votre adresse ...'
Key ='... Votre API key pour Google maps ...'

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        #print('Getting the upcoming 10 events')
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return

        # Prints the start and name of the next 10 events
        gmaps = googlemaps.Client(key=Key)
        for event in events:
            if 'location' in event:
                start = event['start'].get('dateTime', event['start'].get('date'))
                Dest = event['location']
                Hr = event['start'].get('datetime')
                print(f"A {start}, me rendre à {Dest} : {event['summary']}.")
                route = gmaps.directions(Depart, Dest, mode='driving', arrival_time=Hr, units='metric')
                Distance = route[0]['legs'][0]['distance']['value']/1000
                Durée = route[0]['legs'][0]['duration']['value']/60
                print(f"   distance:{Distance:4.1f} Kms, durée:{Durée:4.1f} minutes.")

    except HttpError as error:
        print('An error occurred: %s' % error)


if __name__ == '__main__':
    main()