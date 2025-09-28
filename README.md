# GmailReader

GmailReader listens for new Gmail messages through Google Pub/Sub, extracts the email content and passes it into custom filtering logic (`filterEmail`).

---

## Setup

1. **Google Cloud Setup**
   - Create a project in [Google Cloud Console](https://console.cloud.google.com/).
   - Enable the **Gmail API** and **Pub/Sub API**.
   - Create a Pub/Sub topic and subscription for Gmail push notifications.

2. **Credentials**
   - Download an OAuth **client_secret.json** for Gmail API (Desktop client).
   - Run the script once to generate `token.json` (stored OAuth token).
   - Create a **service account** with Pub/Sub subscriber rights and export its key JSON.
   - Set the env variable:  
     export GOOGLE_APPLICATION_CREDENTIALS="/path/to/subscriber_key.json"
     

3. **Run the watch file**
   python pullnewmail.py

## Useful Links
- Gmail API: https://developers.google.com/workspace/gmail/api/reference/rest
- Gmail Push Notifs: https://developers.google.com/workspace/gmail/api/guides/push
- Pub/Sub Docs: https://cloud.google.com/pubsub/docs/overview
- OAuth 2.0 for APIs: https://developers.google.com/identity/protocols/oauth2

# JSON files (not included in GitHub, but referenced in code files)

- **`client_secret.json`** – OAuth client credentials downloaded from Google Cloud, used on first run to obtain the user’s Gmail API access token.  
- **`cursor.json`** – Tracks the last processed Gmail `historyId` so the app can resume syncing from where it left off.  
- **`seen_ids.json`** – Stores Gmail message IDs that have already been processed to avoid duplicates.  
- **`subscriber_key.json`** – Service account key file that authenticates the Pub/Sub subscriber for receiving Gmail push notifications.  
- **`token.json`** – Persisted user OAuth token (access + refresh) generated on first run, enabling ongoing Gmail API access without re-consent.  
- **`calendartoken.json`** – Persisted user OAuth token (access + refresh) generated on first run, enabling ongoing Calendar API access without re-consent.  



