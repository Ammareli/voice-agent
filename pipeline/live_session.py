# pipeline/live_session.py

import asyncio
import threading
import queue as thread_queue
from google import genai
from google.genai import types

from pipeline.audio_stream import get_input_stream, get_output_stream, terminate
from tools.definitions import TOOL_DEFINITIONS
from tools.gmail_send import send_email
from tools.gmail_read import read_inbox
from config import GEMINI_API_KEY

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={"api_version": "v1beta"}
)

VOICE_NAME = "Aoede"

SYSTEM_PROMPT = """
You are a helpful and polite voice assistant connected to a user's Gmail account.
You speak in short, natural sentences suitable for audio playback.

When the user asks you to check, read, or search emails, call read_inbox.
When they ask you to send an email, compose a message, or write to someone, call send_email.

After a tool call finishes, confirm the action with the user naturally based on
the result you receive.
"""

TOOL_DISPATCH = {
    "send_email": lambda args: send_email(**args),
    "read_inbox": lambda args: read_inbox(**args),
}


def _audio_player_thread(audio_q: thread_queue.Queue, gemini_speaking: threading.Event):
    stream = get_output_stream()
    print("🔊 Audio player thread ready")
    while True:
        chunk = audio_q.get()
        if chunk is None:
            break
        try:
            stream.write(chunk)
        except Exception as e:
            print(f"⚠️  Audio write error: {e}")
    stream.stop_stream()
    stream.close()


async def _stream_mic(session, gemini_speaking: threading.Event):
    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()

    def callback(in_data, frame_count, time_info, status):
        loop.call_soon_threadsafe(queue.put_nowait, in_data)
        return (None, 0)

    stream = get_input_stream(callback)
    stream.start_stream()
    print("🎙️  Mic active — speak your command!\n")

    try:
        while True:
            chunk = await queue.get()

            # ── Mute gate: drop mic audio while Gemini is speaking ──────────
            if gemini_speaking.is_set():
                continue
            # ────────────────────────────────────────────────────────────────

            await session.send_realtime_input(
                audio=types.Blob(
                    data=chunk,
                    mime_type="audio/pcm;rate=16000"
                )
            )
    except asyncio.CancelledError:
        raise
    except Exception as e:
        print(f"❌ Mic stream died: {e}")
        raise
    finally:
        stream.stop_stream()
        stream.close()
        print("🎙️  Mic stream closed.")


async def run_live():
    loop = asyncio.get_event_loop()

    # Shared flag: set while Gemini audio is playing, mic is gated off
    gemini_speaking = threading.Event()

    audio_q = thread_queue.Queue()
    player_thread = threading.Thread(
        target=_audio_player_thread,
        args=(audio_q, gemini_speaking),
        daemon=True
    )
    player_thread.start()

    config = types.LiveConnectConfig(
        system_instruction=types.Content(parts=[types.Part.from_text(text=SYSTEM_PROMPT)]),
        tools=[{"function_declarations": TOOL_DEFINITIONS}],
        response_modalities=["audio"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=VOICE_NAME
                )
            )
        )
    )

    async with client.aio.live.connect(model="gemini-2.5-flash-native-audio-latest", config=config) as session:
        print("\n=======================================================")
        print("🔗 Connected to Gemini Live!")
        print("⏹️  Press Ctrl+C to stop.")
        print("=======================================================\n")

        await session.send_client_content(
        turns=types.Content(
            role="user",
            parts=[types.Part.from_text(
                text="Please greet the user and introduce yourself as their Gmail voice assistant."
            )]
        ),
        turn_complete=True
)
        print("⏳ Waiting for greeting...\n")

        mic_task = asyncio.create_task(_stream_mic(session, gemini_speaking))

        greeting_done = False

        try:
            while True:
                async for response in session.receive():

                    if response.server_content is not None:
                        model_turn = response.server_content.model_turn
                        if model_turn is not None:
                            for part in model_turn.parts:
                                if part.inline_data is not None:
                                    gemini_speaking.set()       # ← gate mic off
                                    audio_q.put_nowait(part.inline_data.data)

                        if response.server_content.turn_complete:
                            # Small delay so the last audio chunk finishes
                            # playing before the mic reopens
                            await asyncio.sleep(0.4)
                            gemini_speaking.clear()             # ← gate mic on
                            if not greeting_done:
                                greeting_done = True
                                print("✅ Greeting done — speak now!\n")
                            else:
                                print("✅ Response done — listening...\n")

                    if response.tool_call is not None:
                        for fc in response.tool_call.function_calls:
                            name = fc.name
                            args = dict(fc.args)
                            print(f"\n⚙️  [Tool call] {name}({args})")
                            try:
                                result = await loop.run_in_executor(
                                    None, TOOL_DISPATCH[name], args
                                )
                            except Exception as e:
                                print(f"❌  [Tool error] {e}")
                                result = f"Error executing {name}: {e}"
                            print(f"✅  [Tool result]\n{result}\n")

                            await session.send_tool_response(
                                function_responses=[
                                    types.FunctionResponse(
                                        id=fc.id,
                                        name=name,
                                        response={"result": result}
                                    )
                                ]
                            )

                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            import traceback
            print(f"❌ Session error: {e}")
            traceback.print_exc()
        finally:
            mic_task.cancel()
            audio_q.put(None)
            player_thread.join(timeout=2)
            print("\n👋 Session ended.")