"""
utils/contact_resolver.py
─────────────────────────
Maps a friendly name ("alice") to a full email address ("alice@example.com").

Resolution order
----------------
1. If the value already looks like an email address, return it unchanged.
2. Look up the lowercased name in the CONTACTS dict loaded from .env.
3. If still unresolved, return the original value and let the caller decide
   whether to abort or ask the user for clarification.
"""

import re
from config import CONTACTS

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def resolve(name_or_email: str) -> str:
    """
    Resolve a friendly name or raw email to a confirmed email address.

    Parameters
    ----------
    name_or_email : str
        Either a full email address or a friendly name from the contacts map.

    Returns
    -------
    str
        The resolved email address (or the original string if unresolved).
    """
    value = name_or_email.strip()

    # Already an email? Fast-path return.
    if _EMAIL_RE.match(value):
        return value

    # Try a case-insensitive lookup in CONTACTS
    resolved = CONTACTS.get(value.lower())
    if resolved:
        print(f"📒 Resolved contact: '{value}' → {resolved}")
        return resolved

    # Not found — return as-is (caller handles the "unknown contact" case)
    print(f"⚠️  Contact '{value}' not found in contacts map — using as-is.")
    return value
