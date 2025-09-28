# Not important

import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

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

def gmail_send_message():
    creds = get_user_creds()
    try:
        service = build("gmail", "v1", credentials=creds)
        message = EmailMessage()
        message.set_content("New Message")
        message["To"] = "swastiksp25@gmail.com"
        message["From"] = "seanrambil@gmail.com"  # 'me' = authorized account
        message["Subject"] = "Automated draft"
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {"raw": encoded_message}
        sent = service.users().messages().send(userId="me", body=body).execute()
        print(f"Message Id: {sent['id']}")
        return sent
    except HttpError as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    gmail_send_message()
