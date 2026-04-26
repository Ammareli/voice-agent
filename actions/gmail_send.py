"""
actions/gmail_send.py
─────────────────────
Composes and sends an email using the Gmail API.

The recipient's "to" value goes through contact_resolver first so that
friendly names like "alice" become "alice@example.com" automatically.
"""

import base64
from email.mime.text import MIMEText

from auth.google_oauth import get_gmail_service
from utils.contact_resolver import resolve
from config import GMAIL_SENDER_ADDRESS


def send_email(to: str, subject: str, body: str) -> dict:
    """
    Send an email via the Gmail API.

    Parameters
    ----------
    to : str
        Recipient name or email address.
    subject : str
        Email subject line.
    body : str
        Plain-text email body.

    Returns
    -------
    dict
        The Gmail API response (contains message id, thread id, etc.)

    Raises
    ------
    ValueError
        If the resolved recipient doesn't contain '@' (unresolvable contact).
    googleapiclient.errors.HttpError
        If the Gmail API call fails.
    """
    recipient = resolve(to)

    if "@" not in recipient:
        raise ValueError(
            f"Could not resolve a valid email address for '{to}'.\n"
            f"Add it to your CONTACTS_JSON in .env:  \"{to.lower()}\": \"email@example.com\""
        )

    # Build the MIME message
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

    print(f"✉️  Email sent to {recipient} | subject: '{subject}' | id: {result.get('id')}")
    return result
