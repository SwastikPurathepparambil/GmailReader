# All good
# Not important
import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os


# Various scopes exist here:
# Full Access
# https://mail.google.com/

# Read Gmail messages and settings (no modification)
# https://www.googleapis.com/auth/gmail.readonly

# Read and modify (but not delete) Gmail messages and labels
# https://www.googleapis.com/auth/gmail.modify

# Create, read, update, and delete drafts. Send messages
# https://www.googleapis.com/auth/gmail.compose

# Send messages only
# https://www.googleapis.com/auth/gmail.send

SCOPES = ["https://mail.google.com/"]

def get_user_creds():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # USE OAuth CLIENT JSON FILE HERE:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=8080, redirect_uri_trailing_slash=True)

        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return creds

def quickstart():
    creds = get_user_creds()
    try:
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId="me", q="is:unread").execute()
        # messages = results.get()
        # labels = results.get("labels", [])

        if not results:
            print("No results found.")
            return
        
        print("Result:")
        # for label in labels:
        #     print(label["name"])
        print(results)

    except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    quickstart()