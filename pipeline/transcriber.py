"""
pipeline/transcriber.py
───────────────────────
Sends a .wav file to Groq Whisper large-v3 and returns the transcript string.
"""

from pathlib import Path
from groq import Groq
from config import GROQ_API_KEY, STT_MODEL


def transcribe(audio_path: str) -> str:
    """
    Transcribe a WAV file using Groq Whisper.

    Parameters
    ----------
    audio_path : str
        Absolute or relative path to the .wav file.

    Returns
    -------
    str
        The transcribed text, stripped of leading/trailing whitespace.

    Raises
    ------
    FileNotFoundError
        If the audio file does not exist.
    groq.APIError
        If the Groq API request fails.
    """
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    client = Groq(api_key=GROQ_API_KEY)

    print(f"📡 Transcribing '{path.name}' via Groq Whisper ({STT_MODEL})…")

    with open(path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            file=(path.name, audio_file),
            model=STT_MODEL,
            response_format="text",      # plain string back
            language="en",
        )

    # response is a plain string when response_format="text"
    transcript: str = response.strip() if isinstance(response, str) else response.text.strip()

    print(f"📝 Transcript: \"{transcript}\"")
    return transcript
