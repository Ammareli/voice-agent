# pipeline/audio_stream.py

import pyaudio

CHUNK      = 1024
FORMAT     = pyaudio.paInt16
CHANNELS   = 1
INPUT_RATE  = 16_000
OUTPUT_RATE = 24_000

_pa = pyaudio.PyAudio()

def get_input_stream(callback) -> pyaudio.Stream:
    return _pa.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=INPUT_RATE,
        input=True,
        frames_per_buffer=CHUNK,
        stream_callback=callback,
        start=False,
    )

def get_output_stream() -> pyaudio.Stream:
    return _pa.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=OUTPUT_RATE,
        output=True,
        frames_per_buffer=CHUNK,
    )

def terminate():
    _pa.terminate()