import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

def get_google_service(
    api_name,
    api_version,
    scopes,
    credentials_file: str = "client_secret.json",
    token_file: str = "token.json",
    port: int = 8080,
    access_type: str = "offline",
    prompt: str = "consent",
    redirect_uri_trailing_slash: bool = True,
):

    if isinstance(scopes, str):
        scopes = [scopes]

    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
            creds = flow.run_local_server(
                port=port,
                redirect_uri_trailing_slash=redirect_uri_trailing_slash,
                access_type=access_type,
                prompt=prompt,
            )
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return build(api_name, api_version, credentials=creds)
