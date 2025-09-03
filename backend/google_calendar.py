import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz



def get_calendar_timezone(credentials: Credentials) -> str:
    #creds = get_creds()
    service = build("calendar", "v3", credentials=credentials)
    try:
      calendar = service.calendars().get(calendarId='primary').execute()
      return calendar.get('timeZone','UTC')
    except:
      return 'UTC'


def fetch_date_events(credentials: Credentials ,start_date, timezone):
  service = build("calendar", "v3", credentials=credentials)

  try:

    start_of_day = datetime.datetime(
        year=start_date.year,
        month=start_date.month,
        day=start_date.day,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )
    tz = pytz.timezone(timezone)
    now = tz.localize(start_of_day)
    tomorrow = (now + datetime.timedelta(days=1)).isoformat()
    now = now.isoformat()
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            timeMax = tomorrow,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    # Prints the start and name of the next 10 events
    for event in events:
      
      start = event["start"].get("dateTime", event["start"].get("date"))
      print(start, event["summary"])
    
    return events

  except HttpError as error:
    print(f"An error occurred: {error}")

def get_email_id(event):
  desc = event.get('description', None)
  if not desc:
    return None
  
  email_id = eval(desc).get('email_id', 'None')

  return email_id


def add_events(credentials: Credentials, email_id, event, timezone):
  #creds = get_creds()
  service = build("calendar", "v3", credentials=credentials)
  tmp = {'email_id':email_id, 'summary':event['event_summary']}

  try:
    # Call the Calendar API.
    event = {
      'summary': event['event_name'],
      'description': str(tmp),
      'start': {
        'dateTime': datetime.datetime.fromisoformat(event['event_start']).isoformat(),
        'timeZone': timezone
      },
      'end': {
        'dateTime': datetime.datetime.fromisoformat(event['event_end']).isoformat(),
        'timeZone': timezone
      }
    }
    result = service.events().insert(calendarId='primary', body=event).execute()
    return result
  except HttpError as error:
    print(f"An error occurred: {error}")


"""if __name__ == "__main__":
  fetch_date_events(credentials=creds, start_date=datetime.datetime(2025, 8, 28, 19, 0), timezone='Australia/Sydney')"""