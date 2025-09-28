# All good
# Not important
import datetime
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDENTIALS_FILE = "client_secret.json"
TOKEN_FILE = "calendartoken.json"

def get_user_creds():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use your downloaded OAuth client JSON file here:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(
                port=8080, 
                redirect_uri_trailing_slash=True,
                access_type="offline",
                prompt="consent"
            )

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds

def list_upcoming_events():
    creds = get_user_creds()
    service = build("calendar", "v3", credentials=creds)
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC
    events_result = (service.events()
                     .list(calendarId="primary", timeMin=now,
                           maxResults=10, singleEvents=True,
                           orderBy="startTime")
                     .execute())
    events = events_result.get("items", [])
    if not events:
        print("No upcoming events found.")
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event.get('summary'))

if __name__ == "__main__":
    list_upcoming_events()
