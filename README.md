# 🎙️ Voice-to-Action Gmail Bot

A portfolio project that converts natural voice commands into Gmail actions — send emails and read your inbox — using **Groq Whisper large-v3** (STT) and **Qwen3-32b** (intent extraction).

```
User speaks → Groq Whisper (STT) → Qwen3-32b (intent) → Action Router → Gmail API
```

**Total latency after speaking: ~1–2.5 s** — fast enough for a responsive voice assistant, thanks to Groq's LPU inference.

---

## Features

| Voice command | Action |
|---|---|
| "Send John an email about the meeting tomorrow" | `send_email` |
| "Email Sarah the project update" | `send_email` |
| "Read my inbox" / "What are my latest emails?" | `read_inbox` |
| "Search for emails from David" | `read_inbox` with query |

---

## Tech Stack

| Component | Library / Service |
|---|---|
| Voice recording | `sounddevice` + `scipy` |
| Speech-to-text | Groq — `whisper-large-v3` |
| Intent extraction | Groq — `qwen/qwen3-32b` |
| Gmail integration | `google-api-python-client` |
| Gmail auth | `google-auth-oauthlib` |
| Config management | `python-dotenv` |

---

## Project Structure

```
agent_bot/
├── main.py                   # Entry point — full pipeline + CLI flags
├── config.py                 # Loads all env vars / API keys
├── .env                      # 🔒 Your secrets (never commit)
├── .env.example              # Template — copy and fill in
│
├── pipeline/
│   ├── recorder.py           # Mic → .wav (fixed or silence-detection mode)
│   ├── transcriber.py        # .wav → transcript (Groq Whisper)
│   └── intent_extractor.py  # transcript → JSON action (Qwen3-32b)
│
├── actions/
│   ├── router.py             # Dispatches action dict to the right handler
│   ├── gmail_send.py         # Sends email via Gmail API
│   └── gmail_read.py         # Reads / searches inbox via Gmail API
│
├── auth/
│   ├── google_oauth.py       # OAuth2 flow + token.json refresh
│   ├── credentials.json      # 🔒 Download from Google Cloud Console
│   └── token.json            # 🔒 Auto-generated after first login
│
├── utils/
│   └── contact_resolver.py  # Maps "alice" → "alice@example.com"
│
├── requirements.txt
└── README.md
```

---

## Setup

### 1 — Install dependencies

```bash
pip install -r requirements.txt
```

> **Linux mic fix:** if `sounddevice` can't find your mic, install PortAudio:
> ```bash
> sudo apt-get install portaudio19-dev
> ```

### 2 — Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
GROQ_API_KEY=gsk_...          # https://console.groq.com
GMAIL_SENDER_ADDRESS=you@gmail.com

# Optional friendly-name → email map
CONTACTS_JSON={"alice": "alice@example.com", "bob": "bob@work.com"}
```

### 3 — Set up Gmail OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com).
2. Create a project → **Enable the Gmail API**.
3. Go to **APIs & Services → Credentials → Create OAuth 2.0 Client ID** (Desktop app).
4. Download **`credentials.json`** → place it in the `auth/` folder.
5. On first run the bot opens a browser for your consent and saves `auth/token.json` automatically.

### 4 — Run

```bash
# Full voice pipeline (mic → Whisper → Qwen3 → Gmail)
python main.py

# Text mode — type commands instead of speaking (great for testing)
python main.py --text

# Run once and exit (no loop)
python main.py --once

# Combine: type one command and exit
python main.py --text --once
```

---

## Recorder Modes

Set `RECORDER_MODE` in `.env`:

| Value | Behaviour |
|---|---|
| `fixed` (default) | Records for `RECORDING_DURATION_SECONDS` seconds (default 5) |
| `silence` | Records until silence is detected; stops after `SILENCE_TIMEOUT_SECONDS` (default 1.5 s) |

```env
RECORDER_MODE=silence
SILENCE_THRESHOLD=0.01
SILENCE_TIMEOUT_SECONDS=1.5
MAX_RECORDING_SECONDS=30
```

---

## Extending the Bot

To add a new action (e.g., create a calendar event):

1. Create `actions/calendar_action.py` with a `create_event(**kw)` function.
2. Register it in `actions/router.py`:
   ```python
   "create_event": lambda **kw: create_event(**kw),
   ```
3. Add the JSON schema to the system prompt in `pipeline/intent_extractor.py`.

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ | — | Groq API key |
| `GMAIL_SENDER_ADDRESS` | ✅ | — | From address for sent emails |
| `CONTACTS_JSON` | ❌ | `{}` | JSON map of name → email |
| `RECORDER_MODE` | ❌ | `fixed` | `fixed` or `silence` |
| `RECORDING_DURATION_SECONDS` | ❌ | `5` | Fixed recording length |
| `RECORDING_SAMPLE_RATE` | ❌ | `16000` | Audio sample rate (Hz) |
| `RECORDING_OUTPUT_PATH` | ❌ | `/tmp/voice_command.wav` | WAV output path |
| `SILENCE_THRESHOLD` | ❌ | `0.01` | RMS amplitude below = silence |
| `SILENCE_TIMEOUT_SECONDS` | ❌ | `1.5` | Silence duration before stop |
| `MAX_RECORDING_SECONDS` | ❌ | `30` | Hard cap on recording length |
| `STT_MODEL` | ❌ | `whisper-large-v3` | Groq STT model |
| `INTENT_MODEL` | ❌ | `qwen/qwen3-32b` | Groq LLM model |

---

## Security Notes

- **Never commit** `.env`, `auth/credentials.json`, or `auth/token.json`.
- All three are listed in `.gitignore`.
- `token.json` is refreshed silently when expired — you only need browser login once.
