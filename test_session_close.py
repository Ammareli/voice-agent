import asyncio
from google import genai
from google.genai import types
import os

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "dummy"))

async def main():
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
    )
    try:
        async with client.aio.live.connect(model="gemini-3.1-flash-live-preview", config=config) as session:
            await session.send_realtime_input(text="Hello")
            async for resp in session.receive():
                print("Got response")
                break
    except Exception as e:
        print("Error:", e)

asyncio.run(main())
