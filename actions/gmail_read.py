"""
actions/gmail_read.py
─────────────────────
Fetches and displays emails from the inbox (or a search query).
Uses Gmail API  users.messages.list  +  users.messages.get.
"""

from auth.google_oauth import get_gmail_service


def _get_header(headers: list[dict], name: str) -> str:
    """Extract a single header value by name (case-insensitive)."""
    name_lower = name.lower()
    for h in headers:
        if h.get("name", "").lower() == name_lower:
            return h.get("value", "")
    return "(unknown)"


def read_inbox(query: str | None = None, max_results: int = 5) -> list[dict]:
    """
    Fetch emails from the inbox (optionally filtered by a search query).

    Parameters
    ----------
    query : str | None
        Gmail search query (e.g. "from:david", "subject:report").
        Pass None or "" to list the most recent inbox messages.
    max_results : int
        Maximum number of messages to fetch and display.

    Returns
    -------
    list[dict]
        A list of message summaries, each with keys:
        id, from, subject, date, snippet.
    """
    service = get_gmail_service()

    list_params: dict = {
        "userId": "me",
        "maxResults": max_results,
        "labelIds": ["INBOX"],
    }
    if query:
        list_params["q"] = query
        print(f"🔍 Searching inbox for: '{query}' (max {max_results})")
    else:
        print(f"📬 Fetching {max_results} latest inbox messages…")

    list_response = service.users().messages().list(**list_params).execute()
    message_stubs = list_response.get("messages", [])

    if not message_stubs:
        print("📭 No messages found.")
        return []

    results = []
    for stub in message_stubs:
        msg = (
            service
            .users()
            .messages()
            .get(userId="me", id=stub["id"], format="metadata",
                 metadataHeaders=["From", "Subject", "Date"])
            .execute()
        )
        headers = msg.get("payload", {}).get("headers", [])
        summary = {
            "id":      msg["id"],
            "from":    _get_header(headers, "From"),
            "subject": _get_header(headers, "Subject"),
            "date":    _get_header(headers, "Date"),
            "snippet": msg.get("snippet", ""),
        }
        results.append(summary)

    # ── Pretty-print ───────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    for i, m in enumerate(results, start=1):
        print(f"[{i}] From:    {m['from']}")
        print(f"    Subject: {m['subject']}")
        print(f"    Date:    {m['date']}")
        print(f"    Snippet: {m['snippet'][:120]}…")
        print()
    print(f"{'─' * 60}\n")

    return results
