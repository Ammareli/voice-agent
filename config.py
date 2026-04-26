"""
config.py — centralised settings loaded from .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (one level above this file if needed)
load_dotenv(dotenv_path=Path(__file__).parent / ".env")


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(
            f"Missing required environment variable: {key}\n"
            f"Copy .env.example → .env and fill in the value."
        )
    return val


# ── Groq ───────────────────────────────────────────────────────────────────
GROQ_API_KEY: str = _require("GROQ_API_KEY")

# ── Gmail ──────────────────────────────────────────────────────────────────
GMAIL_SENDER_ADDRESS: str = _require("GMAIL_SENDER_ADDRESS")

# ── Pipeline tuning ────────────────────────────────────────────────────────
RECORDING_DURATION_SECONDS: int = int(os.getenv("RECORDING_DURATION_SECONDS", "5"))
RECORDING_SAMPLE_RATE: int = int(os.getenv("RECORDING_SAMPLE_RATE", "16000"))
RECORDING_OUTPUT_PATH: str = os.getenv("RECORDING_OUTPUT_PATH", "/tmp/voice_command.wav")

STT_MODEL: str = os.getenv("STT_MODEL", "whisper-large-v3")
INTENT_MODEL: str = os.getenv("INTENT_MODEL", "qwen/qwen3-32b")

# ── Contacts ───────────────────────────────────────────────────────────────
import json as _json
_raw_contacts = os.getenv("CONTACTS_JSON", "{}")
try:
    CONTACTS: dict[str, str] = _json.loads(_raw_contacts)
except _json.JSONDecodeError:
    CONTACTS = {}
