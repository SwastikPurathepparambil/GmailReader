import re
import os
import json
import base64
from google.cloud import pubsub_v1
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from filtermail import filterEmail
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.types import FlowControl
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from tools import get_google_service

SCOPES = ["https://mail.google.com/"]
PROJECT_ID = "emailreader-472800"
SUBSCRIPTION_ID = "gmail-updates-sub"
CURSOR_FILE = "cursor.json"
SEEN_FILE = "seen_ids.json"

# checks for previously seen messages so we don't get repeats
def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)



def _b64url_decode(data):
    # Gmail uses base64url without padding; add it back if needed.
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def _first(part_list, mime_prefix):
    # Return the first part whose mimeType starts with mime_prefix
    for p in part_list or []:
        if p.get("mimeType", "").startswith(mime_prefix):
            return p
    return None

def extract_body_from_message(msg, prefer="plain"):
    """
    Returns (text, mimeType) from a Gmail message resource.
    prefer: "plain" (default) or "html"
    """
    payload = msg.get("payload", {})
    mimeType = payload.get("mimeType", "")
    data_field = payload.get("body", {}).get("data")

    # Single-part messages
    if data_field and (mimeType.startswith("text/")):
        text = _b64url_decode(data_field).decode("utf-8", errors="replace")
        return text, mimeType

    parts = payload.get("parts", [])
    if not parts:
        return "", ""

    # If multipart/alternative, look for text/plain (or html) by preference
    if prefer == "plain":
        part = _first(parts, "text/plain") or _first(parts, "text/html")
    else:
        part = _first(parts, "text/html") or _first(parts, "text/plain")

    if part and part.get("body", {}).get("data"):
        text = _b64url_decode(part["body"]["data"]).decode("utf-8", errors="replace")
        return text, part.get("mimeType", "")

    # Some emails nest parts deeper (e.g., mixed → alternative)
    # Walk recursively until we find a text part
    stack = parts[:]
    while stack:
        p = stack.pop()
        if p.get("body", {}).get("data") and p.get("mimeType", "").startswith("text/"):
            text = _b64url_decode(p["body"]["data"]).decode("utf-8", errors="replace")
            return text, p.get("mimeType", "")
        stack.extend(p.get("parts", []) or [])

    return "", ""

def load_cursor():
    try:
        with open(CURSOR_FILE) as f:
            return json.load(f)["historyId"]
    except FileNotFoundError:
        return None

def save_cursor(history_id):
    with open(CURSOR_FILE, "w") as f:
        json.dump({"historyId": history_id}, f)

def header(headers, name):
    for h in headers:
        if h["name"] == name:
            return h["value"]
    return ""

def process_changes(service, start_history_id):
    if not start_history_id:
        profile = service.users().getProfile(userId="me").execute()
        save_cursor(profile["historyId"])
        print("Bootstrapped historyId:", profile["historyId"])
        return profile["historyId"]

    resp = service.users().history().list(
        userId="me",
        startHistoryId=start_history_id,
        historyTypes=["messageAdded"],
    ).execute()

    latest_id = start_history_id
    seen = load_seen()  # load previously seen message IDs

    for h in resp.get("history", []):
        latest_id = h["id"]
        for m in h.get("messagesAdded", []):
            msg_id = m["message"]["id"]

            # skip if already processed
            if msg_id in seen:
                continue

            msg = service.users().messages().get(
                userId="me",
                id=msg_id,
                format="full"
            ).execute()

            # Headers (From, Subject)
            headers = msg["payload"]["headers"]
            from_ = header(headers, "From")
            subject = header(headers, "Subject")

            # Body (prefer text/plain, fallback to text/html)
            body_text, mime = extract_body_from_message(msg, prefer="plain")
            if mime == "text/html":
                body_printable = re.sub(r"<[^>]+>", "", body_text)
            else:
                body_printable = body_text

            # filter email
            filterEmail(sender=from_, subject=subject, body=body_printable)

            # mark as processed
            seen.add(msg_id)

    if latest_id != start_history_id:
        save_cursor(latest_id)
    save_seen(seen)
    return latest_id





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
            creds = flow.run_local_server(
                port=8080, 
                redirect_uri_trailing_slash=True,
                access_type="offline",
                prompt="consent"
            )

        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return creds

def pullmail():
    # Load Gmail creds from your token.json
    service = get_google_service(
        api_name="gmail",
        api_version="v1",
        scopes=SCOPES,
        credentials_file="client_secret.json",
        token_file="token.json",
    )

    # IF THE ENVIRONMENT GETS RESET
    # NEED TO export GOOGLE_APPLICATION_CREDENTIALS="/Users/swastik/Desktop/gmailreader/subscriber_key.json"
    # Pub/Sub subscriber (needs GOOGLE_APPLICATION_CREDENTIALS env var set to a service account JSON)
    
    subscriber = pubsub_v1.SubscriberClient()
    sub_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    if not load_cursor():
        process_changes(service, None)

    def callback(message: pubsub_v1.subscriber.message.Message):
        try:
            message.ack()
            # Each notification => fetch changes since last cursor
            start_hid = load_cursor()
            process_changes(service, start_hid)
        except Exception as e:
            print("Callback error:", e)
    
    flow = FlowControl(max_messages=1)  # pull 1 at a time

    streaming_future = subscriber.subscribe(
        sub_path,
        callback=callback,
        flow_control=flow,
    )
    print("Listening for new emails… Ctrl+C to stop")

    try:
        streaming_future.result()  # blocks forever; auto-reconnects
    except KeyboardInterrupt:
        streaming_future.cancel()


if __name__ == "__main__":
    pullmail()