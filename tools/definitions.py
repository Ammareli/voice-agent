"""
tools/definitions.py
────────────────────
Gemini Live-compatible function declaration schemas.

Gemini reads these at session start and decides autonomously when to invoke
them. Descriptions must be explicit — Gemini uses them as routing signals.
"""

TOOL_DEFINITIONS = [
    {
        "name": "send_email",
        "description": (
            "Send an email to a person. Call this whenever the user asks you to "
            "send, write, compose, or email someone a message. "
            "Resolve friendly names (e.g. 'alice') automatically — do NOT ask the "
            "user for an email address if a name is provided."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": (
                        "Recipient email address OR a friendly name from the contacts "
                        "map (e.g. 'alice'). The function resolves names automatically."
                    ),
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line.",
                },
                "body": {
                    "type": "string",
                    "description": "Plain-text email body.",
                },
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "read_inbox",
        "description": (
            "Read recent emails from the Gmail inbox. Call this when the user asks "
            "you to check, read, fetch, list, or summarise their email or inbox. "
            "Use the query parameter for specific searches like 'from:alice' or "
            "'subject:report' or 'is:unread'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Gmail search query string, e.g. 'from:alice', 'is:unread', "
                        "'subject:invoice'. Leave empty to fetch the latest messages."
                    ),
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of emails to return. Defaults to 5.",
                },
            },
            "required": [],
        },
    },
]
