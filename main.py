"""
main.py
───────
Entry point for the Voice-to-Action Gmail Bot.

Pipeline
--------
  record() → transcribe() → extract_intent() → dispatch()

Run modes
---------
  python main.py              # full voice pipeline (mic → Whisper → Qwen3 → Gmail)
  python main.py --text       # skip recording; type your command instead (great for testing)
  python main.py --once       # run the pipeline once and exit (no loop)
"""

import argparse
import sys
import time


def _banner() -> None:
    print("""
╔══════════════════════════════════════════════════════╗
║        🎙️  Voice-to-Action Gmail Bot  📧             ║
║   Groq Whisper (STT)  +  Qwen3-32b (intent)         ║
╚══════════════════════════════════════════════════════╝
Type  Ctrl+C  to quit at any time.
""")


def run_once(text_mode: bool = False) -> None:
    """Execute the full pipeline exactly one time."""

    # ── Step 1: Get input ──────────────────────────────────────────────────
    if text_mode:
        try:
            transcript = input("💬 Enter your command: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Bye!")
            sys.exit(0)
        if not transcript:
            print("⚠️  Empty input — skipping.")
            return
    else:
        from pipeline.recorder import record
        audio_path = record()

        from pipeline.transcriber import transcribe
        transcript = transcribe(audio_path)
        if not transcript:
            print("⚠️  Empty transcript — try speaking more clearly.")
            return

    # ── Step 2: Extract intent ─────────────────────────────────────────────
    from pipeline.intent_extractor import extract_intent
    action = extract_intent(transcript)

    # ── Step 3: Dispatch to Gmail ──────────────────────────────────────────
    from actions.router import dispatch
    dispatch(action)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Voice-to-Action Gmail Bot — speak a command, watch it happen."
    )
    parser.add_argument(
        "--text", "-t",
        action="store_true",
        help="Use keyboard input instead of microphone (useful for testing).",
    )
    parser.add_argument(
        "--once", "-1",
        action="store_true",
        help="Run the pipeline once and exit (no interactive loop).",
    )
    args = parser.parse_args()

    _banner()

    if args.once:
        run_once(text_mode=args.text)
        return

    # ── Interactive loop ───────────────────────────────────────────────────
    while True:
        try:
            print("─" * 54)
            if args.text:
                print("Ready! (press Enter with empty input to skip)\n")
            else:
                input("Press  Enter  to start recording… (Ctrl+C to quit)\n")

            t0 = time.monotonic()
            run_once(text_mode=args.text)
            elapsed = time.monotonic() - t0
            print(f"⏱️  Total pipeline time: {elapsed:.2f}s\n")

        except KeyboardInterrupt:
            print("\n\n👋 Exiting — goodbye!")
            sys.exit(0)
        except Exception as exc:  # noqa: BLE001
            print(f"\n❌ Unexpected error: {exc}")
            print("   Continuing to next command…\n")


if __name__ == "__main__":
    main()
