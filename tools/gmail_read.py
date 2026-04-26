"""
tools/gmail_read.py
───────────────────
Reads emails from the Gmail inbox and returns a plain-text summary.

Called by the Gemini Live tool-dispatch loop when Gemini emits a
read_inbox function call. Returns a plain-text result string that
Gemini reads aloud / summarises for the user.
"""

from auth.google_oauth import get_gmail_service


def _get_header(headers: list[dict], name: str) -> str:
    """Extract a single header value by name (case-insensitive)."""
    name_lower = name.lower()
    for h in headers:
        if h.get("name", "").lower() == name_lower:
            return h.get("value", "")
    return "(unknown)"


def read_inbox(query: str = "", max_results: int = 5) -> str:
    """
    Fetch recent emails and return a plain-text summary.

    Parameters
    ----------
    query : str
        Gmail search query (e.g. 'from:alice', 'is:unread').
        Empty string → latest inbox messages.
    max_results : int
        Maximum number of messages to fetch.

    Returns
    -------
    str
        Human-readable summary Gemini can speak aloud.
    """
    service = get_gmail_service()

    list_params: dict = {
        "userId": "me",
        "maxResults": max_results,
        "labelIds": ["INBOX"],
    }
    if query:
        list_params["q"] = query
        print(f"🔍 Searching inbox: '{query}' (max {max_results})")
    else:
        print(f"📬 Fetching {max_results} latest inbox messages…")

    list_response = service.users().messages().list(**list_params).execute()
    stubs = list_response.get("messages", [])

    if not stubs:
        return "No emails found matching your request."

    summaries: list[str] = []
    for stub in stubs:
        msg = (
            service
            .users()
            .messages()
            .get(
                userId="me",
                id=stub["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            )
            .execute()
        )
        headers = msg.get("payload", {}).get("headers", [])
        snippet = msg.get("snippet", "")[:120]
        sender  = _get_header(headers, "From")
        subject = _get_header(headers, "Subject")
        summaries.append(
            f"From: {sender}\nSubject: {subject}\nPreview: {snippet}"
        )

    result = "\n\n".join(summaries)
    print(f"\n{'─'*60}\n{result}\n{'─'*60}\n")
    return result
