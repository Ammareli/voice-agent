# main.py

import asyncio
import sys
import struct
import math

from pipeline.live_session import run_live
from pipeline.audio_stream import get_output_stream, terminate   # ← use shared streams

def _banner() -> None:
    print("""
╔══════════════════════════════════════════════════════╗
║        🎙️  Voice-to-Action Gmail Bot  📧             ║
║   Powered by Gemini 2.0 Flash Live API (Realtime)    ║
╚══════════════════════════════════════════════════════╝
""")

def _speaker_test() -> None:
    """Uses the shared _pa from audio_stream — no extra PyAudio instance."""
    stream = get_output_stream()                          # ← shared _pa
    samples = [int(32767 * math.sin(2 * math.pi * 440 * i / 24000))
               for i in range(24000)]
    data = struct.pack(f"{len(samples)}h", *samples)
    stream.write(data)
    stream.stop_stream()
    stream.close()                                        # close the stream, NOT _pa
    print("🔊 Speaker test done — did you hear a beep?\n")

if __name__ == "__main__":
    _banner()
    try:
        _speaker_test()
        asyncio.run(run_live())
    except KeyboardInterrupt:
        print("\n\n👋 Session ended by user. Goodbye!")
    except Exception as e:
        import traceback
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
    finally:
        terminate()                                       # one clean shutdown
        sys.exit(0)