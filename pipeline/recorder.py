"""
pipeline/recorder.py
────────────────────
Records audio from the default microphone and saves it as a WAV file.

Strategy
--------
* Fixed-duration mode (default): records for RECORDING_DURATION_SECONDS seconds.
* Silence-detection mode: keeps recording until the audio level drops below
  SILENCE_THRESHOLD for SILENCE_TIMEOUT_SECONDS consecutive seconds.

Set RECORDER_MODE=silence in .env to enable silence detection.
"""

import os
import time
import numpy as np
import sounddevice as sd
from scipy.io import wavfile

from config import (
    RECORDING_DURATION_SECONDS,
    RECORDING_SAMPLE_RATE,
    RECORDING_OUTPUT_PATH,
)

# ── Silence-detection tunables ─────────────────────────────────────────────
RECORDER_MODE: str = os.getenv("RECORDER_MODE", "fixed")          # "fixed" | "silence"
SILENCE_THRESHOLD: float = float(os.getenv("SILENCE_THRESHOLD", "0.01"))   # RMS amplitude
SILENCE_TIMEOUT_SECONDS: float = float(os.getenv("SILENCE_TIMEOUT_SECONDS", "1.5"))
MAX_RECORDING_SECONDS: int = int(os.getenv("MAX_RECORDING_SECONDS", "30"))


def _rms(chunk: np.ndarray) -> float:
    return float(np.sqrt(np.mean(chunk.astype(np.float64) ** 2)))


def record_fixed(duration: int = RECORDING_DURATION_SECONDS,
                 sample_rate: int = RECORDING_SAMPLE_RATE,
                 output_path: str = RECORDING_OUTPUT_PATH) -> str:
    """
    Record for a fixed number of seconds.
    Returns the path to the saved .wav file.
    """
    print(f"🎙️  Recording for {duration} second(s)… Speak now!")
    audio = sd.rec(
        frames=duration * sample_rate,
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
    )
    sd.wait()
    wavfile.write(output_path, sample_rate, audio)
    print(f"✅ Saved recording → {output_path}")
    return output_path


def record_until_silence(sample_rate: int = RECORDING_SAMPLE_RATE,
                         output_path: str = RECORDING_OUTPUT_PATH) -> str:
    """
    Stream audio and stop when silence is detected for SILENCE_TIMEOUT_SECONDS.
    Returns the path to the saved .wav file.
    """
    chunk_duration = 0.1          # seconds per chunk
    chunk_frames = int(sample_rate * chunk_duration)
    chunks: list[np.ndarray] = []
    silence_start: float | None = None

    print("🎙️  Listening… (stops automatically after silence)")

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16") as stream:
        start_time = time.monotonic()
        while True:
            elapsed = time.monotonic() - start_time
            if elapsed > MAX_RECORDING_SECONDS:
                print(f"⚠️  Max recording time ({MAX_RECORDING_SECONDS}s) reached.")
                break

            chunk, _ = stream.read(chunk_frames)
            chunks.append(chunk.copy())

            if _rms(chunk) < SILENCE_THRESHOLD:
                if silence_start is None:
                    silence_start = time.monotonic()
                elif time.monotonic() - silence_start >= SILENCE_TIMEOUT_SECONDS:
                    print("🤫  Silence detected — stopping.")
                    break
            else:
                silence_start = None   # reset on speech

    if not chunks:
        raise RuntimeError("No audio captured.")

    audio = np.concatenate(chunks, axis=0)
    wavfile.write(output_path, sample_rate, audio)
    print(f"✅ Saved recording → {output_path}")
    return output_path


def record(output_path: str = RECORDING_OUTPUT_PATH) -> str:
    """
    Public entry point.  Dispatches to the correct recording strategy based
    on the RECORDER_MODE environment variable.
    """
    if RECORDER_MODE == "silence":
        return record_until_silence(output_path=output_path)
    return record_fixed(output_path=output_path)
