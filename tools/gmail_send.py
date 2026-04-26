"""
tools/gmail_send.py
───────────────────
Sends an email via the Gmail API.

Called by the Gemini Live tool-dispatch loop when Gemini emits a
send_email function call. Returns a plain-text result string that
Gemini reads aloud to the user.
"""

import base64
from email.mime.text import MIMEText

from auth.google_oauth import get_gmail_service
from utils.contact_resolver import resolve
from config import GMAIL_SENDER_ADDRESS


def send_email(to: str, subject: str, body: str) -> str:
    """
    Compose and send an email.

    Parameters
    ----------
    to : str
        Recipient name or email address. Friendly names are resolved
        against the CONTACTS map in .env automatically.
    subject : str
        Email subject line.
    body : str
        Plain-text email body.

    Returns
    -------
    str
        Human-readable confirmation Gemini can speak aloud.
    """
    recipient = resolve(to)

    if "@" not in recipient:
        return (
            f"I couldn't find an email address for '{to}'. "
            "Please add them to your CONTACTS in .env."
        )

    # Build MIME message
    msg = MIMEText(body, "plain")
    msg["to"]      = recipient
    msg["from"]    = GMAIL_SENDER_ADDRESS
    msg["subject"] = subject

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    service = get_gmail_service()
    result = (
        service
        .users()
        .messages()
        .send(userId="me", body={"raw": raw})
        .execute()
    )

    msg_id = result.get("id", "unknown")
    print(f"✉️  Sent → {recipient} | subject: '{subject}' | id: {msg_id}")
    return f"Email sent to {recipient} with subject '{subject}'."
