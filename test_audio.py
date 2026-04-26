# Run this as a standalone test: python test_mic.py
import pyaudio
import time

pa = pyaudio.PyAudio()

print("Available input devices:")
for i in range(pa.get_device_count()):
    info = pa.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f"  [{i}] {info['name']} — {info['maxInputChannels']} ch @ {int(info['defaultSampleRate'])}Hz")

print("\nOpening default mic for 3 seconds...")
chunks = []

def callback(in_data, frame_count, time_info, status):
    chunks.append(in_data)
    return (None, 0)

try:
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=1024,
        stream_callback=callback,
    )
    stream.start_stream()
    print("🎙️ Recording... speak something!")
    time.sleep(3)
    stream.stop_stream()
    stream.close()
    print(f"✅ Got {len(chunks)} chunks — mic works!")
except Exception as e:
    print(f"❌ Mic failed: {e}")

pa.terminate()