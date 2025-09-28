import os
import datetime as dt
from typing import Dict, Any, Optional, Tuple, List
import pytz
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from tools import get_google_service


BUSINESS_START = 8   # 8 AM
BUSINESS_END   = 22  # 10 PM
SLOT_STEP_MIN  = 15  # scan grid in minutes
SLA_DAYS = {"High": 3, "Medium": 7, "Low": 14}

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN = "calendartoken.json"
CREDENTIALS_FILE = "client_secret.json"
CALENDAR_ID = "primary"

def get_calendar_service():
    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(
                port=8080, redirect_uri_trailing_slash=True,
                access_type="offline", prompt="consent"
            )
        with open(TOKEN, "w") as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)

# -------- Helpers --------
def _freebusy(service, start_iso, end_iso, calendar_id="primary"):
    resp = service.freebusy().query(body={
        "timeMin": start_iso,
        "timeMax": end_iso,
        "items": [{"id": calendar_id}]
    }).execute()
    return resp["calendars"][calendar_id].get("busy", [])

def _round_down(dt_local, minutes):
    q = (dt_local.minute // minutes) * minutes
    return dt_local.replace(minute=q, second=0, microsecond=0)

def _day_bounds(tz, d):
    start = tz.localize(dt.datetime(d.year, d.month, d.day, BUSINESS_START, 0, 0))
    end   = tz.localize(dt.datetime(d.year, d.month, d.day, BUSINESS_END,   0, 0))
    return start, end

def find_latest_slot(service, length_min, importance, tz_name):
    tz = pytz.timezone(tz_name)
    now = dt.datetime.now(tz)
    days = SLA_DAYS.get(importance, SLA_DAYS["Low"])
    window_end = now + dt.timedelta(days=days)

    today = now.date()
    d = window_end.date()

    while d >= today:
        day_start, day_end = _day_bounds(tz, d)

        # On "today", do not schedule in the past; start search window after 'now'
        effective_day_start = max(day_start, _round_down(now, SLOT_STEP_MIN)) if d == today else day_start

        latest_start = day_end - dt.timedelta(minutes=length_min)
        if latest_start < effective_day_start:
            d = d - dt.timedelta(days=1)
            continue

        cur_start = _round_down(latest_start, SLOT_STEP_MIN)
        while cur_start >= effective_day_start:
            cur_end = cur_start + dt.timedelta(minutes=length_min)
            if not _freebusy(service, cur_start.isoformat(), cur_end.isoformat(), CALENDAR_ID):
                return cur_start, cur_end
            cur_start -= dt.timedelta(minutes=SLOT_STEP_MIN)

        d = d - dt.timedelta(days=1)

    return None

def schedule_from_payload(payload):
   
    if not payload.get("isInterview"):
        return {"status": "skipped", "reason": "isInterview is False"}

    importance = str(payload.get("importance") or "Low")
    length_min = int(payload.get("lenOfMeeting") or payload.get("lengthOfInterview") or 90)
    tz_name = payload.get("Time zone") or "America/Los_Angeles"
    summary = payload.get("nameOfMeeting") or "Interview"

    # Optional attendees (uncomment if/when you want to invite others)
    # emails = payload.get("emails") or {}
    # attendees = []
    # if emails.get("me"):        attendees.append({"email": emails["me"]})
    # if emails.get("interview"): attendees.append({"email": emails["interview"]})

    # service = get_calendar_service()
    service = get_google_service(api_name="calendar", api_version="v3", scopes=SCOPES, credentials_file=CREDENTIALS_FILE, token_file=TOKEN)

    slot = find_latest_slot(service, length_min, importance, tz_name)
    if not slot:
        return {"status": "failed", "reason": "No available slot in SLA window"}

    s_local, e_local = slot

    event_body = {
        "summary": summary,
        "description": f"Auto-scheduled interview (latest available slot). Importance: {importance}",
        "start": {"dateTime": s_local.isoformat(), "timeZone": tz_name},
        "end":   {"dateTime": e_local.isoformat(), "timeZone": tz_name},
        # "attendees": attendees,
        "conferenceData": {"createRequest": {"requestId": f"req-{int(dt.datetime.utcnow().timestamp())}"}},
        "reminders": {"useDefault": True}
    }

    created = service.events().insert(
        calendarId=CALENDAR_ID,
        body=event_body,
        conferenceDataVersion=1,
        sendUpdates="all"
    ).execute()

    return {
        "status": "created",
        "eventId": created.get("id"),
        "htmlLink": created.get("htmlLink"),
        "hangoutLink": created.get("hangoutLink"),
        "start": created.get("start"),
        "end": created.get("end"),
        "attendees": created.get("attendees", [])
    }
