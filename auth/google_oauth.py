"""
auth/google_oauth.py
────────────────────
Handles Gmail OAuth2 using google-auth-oauthlib.

Flow
----
1. Look for auth/token.json (saved credentials from a previous run).
2. If it exists and is valid, use it (refresh silently if expired).
3. If it doesn't exist or can't be refreshed, start the OAuth consent
   flow in the browser and save the resulting token.

Required scopes
---------------
* gmail.send  — compose & send
* gmail.readonly — read inbox / search

Place your credentials.json (downloaded from Google Cloud Console) in the
auth/ directory before the first run.
"""

from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ── Paths ──────────────────────────────────────────────────────────────────
_AUTH_DIR = Path(__file__).parent
CREDENTIALS_PATH = _AUTH_DIR / "credentials.json"
TOKEN_PATH = _AUTH_DIR / "token.json"

# ── Scopes ─────────────────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def get_gmail_service():
    """
    Authenticate and return an authorised Gmail API service object.

    Returns
    -------
    googleapiclient.discovery.Resource
        Ready-to-use Gmail API client.

    Raises
    ------
    FileNotFoundError
        If credentials.json is missing.
    """
    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            f"Missing Gmail OAuth credentials: {CREDENTIALS_PATH}\n"
            "Download credentials.json from Google Cloud Console → "
            "APIs & Services → Credentials → OAuth 2.0 Client IDs."
        )

    creds: Credentials | None = None

    # ── Load existing token ────────────────────────────────────────────────
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    # ── Refresh or re-authorise ────────────────────────────────────────────
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing Gmail access token…")
            creds.refresh(Request())
        else:
            print("🌐 Opening browser for Gmail authorisation…")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Persist for future runs
        TOKEN_PATH.write_text(creds.to_json())
        print(f"✅ Token saved → {TOKEN_PATH}")

    service = build("gmail", "v1", credentials=creds)
    return service
