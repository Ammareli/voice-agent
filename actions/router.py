"""
actions/router.py
─────────────────
Dispatches a structured action dict (from intent_extractor) to the correct
action function.

Adding a new action
-------------------
1. Create a new file in actions/ (e.g. actions/calendar_action.py).
2. Import it here and add one line to the ACTION_MAP dict.
3. Add the new schema to the system prompt in pipeline/intent_extractor.py.
"""

from actions.gmail_send import send_email
from actions.gmail_read import read_inbox


# ── Registration table ─────────────────────────────────────────────────────
#   key  →  callable that accepts **kwargs from the action dict
ACTION_MAP: dict[str, callable] = {
    "send_email": lambda **kw: send_email(
        to=kw["to"],
        subject=kw.get("subject", "(no subject)"),
        body=kw.get("body", ""),
    ),
    "read_inbox": lambda **kw: read_inbox(
        query=kw.get("query") or None,
        max_results=int(kw.get("max_results", 5)),
    ),
}


def dispatch(action: dict) -> None:
    """
    Route an action dict to the matching handler.

    Parameters
    ----------
    action : dict
        Must contain at minimum an "action" key.
        All other keys are forwarded to the handler as keyword arguments.

    Raises
    ------
    KeyError
        If a required parameter is missing from the action dict.
    """
    action_key = action.get("action", "unknown")

    if action_key == "unknown":
        raw = action.get("raw", "")
        print(f"❓ Could not understand the command: \"{raw}\"")
        print("   Try: 'Send Alice an email…' or 'Read my inbox'.")
        return

    handler = ACTION_MAP.get(action_key)
    if handler is None:
        print(f"⚠️  Unknown action '{action_key}'. No handler registered.")
        return

    # Strip the "action" key before forwarding
    params = {k: v for k, v in action.items() if k != "action"}

    try:
        handler(**params)
    except (ValueError, KeyError) as exc:
        print(f"❌ Action '{action_key}' failed: {exc}")
