import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os
import json

CURSOR_FILE = "cursor.json"  # stores {"historyId": "12345", "expiration": 1759032829693}
SCOPES = ["https://mail.google.com/"]

def get_user_creds():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use your downloaded OAuth client JSON file here:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=8080, redirect_uri_trailing_slash=True)

        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return creds

def save_cursor(history_id, expiration=None):
    with open(CURSOR_FILE, "w") as f:
        json.dump({"historyId": str(history_id), "expiration": expiration}, f)
    print(f"Saved cursor -> {CURSOR_FILE}: historyId={history_id}, expiration={expiration}")


def watchmail():
    creds = get_user_creds()
    try:
        service = build("gmail", "v1", credentials=creds)
        watch_req = {
            "topicName": "projects/emailreader-472800/topics/gmail-updates",
            "labelIds": ["INBOX"],            # only watch inbox
            "labelFilterAction": "include"    # include only these labels
        }

        resp = service.users().watch(userId="me", body=watch_req).execute()
        
        history_id = resp["historyId"]
        expiration = resp.get("expiration")
        save_cursor(history_id, expiration)
        
        print("History ID:", resp["historyId"])
        print("Expiration:", resp["expiration"])
    except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    watchmail()