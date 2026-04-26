"""
pipeline/intent_extractor.py
────────────────────────────
Sends a natural-language transcript to Qwen3-32b on Groq and extracts a
structured JSON action dict.

Supported output schemas
────────────────────────
Send email:
    { "action": "send_email", "to": "<email>", "subject": "<str>", "body": "<str>" }

Read inbox / search:
    { "action": "read_inbox", "query": "<str|null>", "max_results": <int> }

Unknown / not parseable:
    { "action": "unknown", "raw": "<original transcript>" }
"""

import json
import re
from groq import Groq
from config import GROQ_API_KEY, INTENT_MODEL

# ── System prompt ──────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """
You are an intent-extraction engine for a voice-controlled Gmail assistant.

Your ONLY job is to read the user's transcribed voice command and return a
single JSON object — no markdown, no explanation, no extra text.

Supported actions and their exact schemas:

1. Send an email:
   {"action": "send_email", "to": "<recipient email or name>", "subject": "<subject line>", "body": "<email body>"}

2. Read the inbox or search emails:
   {"action": "read_inbox", "query": "<search query or null>", "max_results": 5}

Rules:
- If the user mentions a person's name but no email, use the name as the "to" value.
  The system will resolve it to an email later.
- Infer a sensible subject line from context if the user doesn't state one explicitly.
- Keep the body natural and concise.
- If the command is unclear or doesn't map to a supported action, return:
  {"action": "unknown", "raw": "<original transcript>"}
- Never output anything outside the JSON object.
""".strip()


def extract_intent(transcript: str) -> dict:
    """
    Extract a structured action dict from a free-text voice transcript.

    Parameters
    ----------
    transcript : str
        The raw text from the speech-to-text step.

    Returns
    -------
    dict
        A dict with at minimum an "action" key.
    """
    client = Groq(api_key=GROQ_API_KEY)

    print(f"🧠 Extracting intent via {INTENT_MODEL}…")

    response = client.chat.completions.create(
        model=INTENT_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": transcript},
        ],
        response_format={"type": "json_object"},
        temperature=0.6,
        max_completion_tokens=4096,
        top_p=0.95,
        reasoning_effort="default",
    )

    raw_content: str = response.choices[0].message.content or ""

    # Strip any accidental markdown fences just in case
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_content.strip(), flags=re.MULTILINE)

    try:
        action = json.loads(cleaned)
    except json.JSONDecodeError:
        # Graceful fallback
        action = {"action": "unknown", "raw": transcript}

    print(f"🎯 Intent: {json.dumps(action, indent=2)}")
    return action
