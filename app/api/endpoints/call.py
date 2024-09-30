from fastapi import HTTPException, APIRouter, Request, FastAPI, Form
from pathlib import Path
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import os
import time
from pyht import Client
from pyht.client import TTSOptions, Format
from app.services.stream_gpt_text import stream_gpt_text
from dotenv import load_dotenv
load_dotenv()

router = APIRouter()
is_all_credentials_passed = all([
    os.getenv(c) is not None
    for c in ["PLAY_HT_USER_ID", "PLAY_HT_API_KEY", "OPENAI_API_KEY"]
])

if os.getenv("PLAY_HT_USER_ID") and os.getenv("PLAY_HT_API_KEY"):
  pht_client = Client(
      user_id=os.getenv("PLAY_HT_USER_ID"),
      api_key=os.getenv("PLAY_HT_API_KEY"),
  )
else:
  pht_client = None

@router.get("/say-prompt/")
async def say_prompt(prompt: str):
  headers = dict()

  options = TTSOptions(
      voice="s3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json",
      format=Format.FORMAT_MP3)

  def print_gpt_ttfb(ttfb):
    headers["X-ChatGPT-TTFB"] = str(ttfb)

  gpt_stream = stream_gpt_text(prompt, print_gpt_ttfb)

  def audio_generator():
    is_first_chunk = True
    start_time = int(time.time() * 1000)
    for chunk in pht_client.stream_tts_input(gpt_stream, options):
      if is_first_chunk:
        is_first_chunk = False
        end_time = int(time.time() * 1000)
        play_ht_ttfb = end_time - start_time

        chat_gpt_ttb = headers["X-ChatGPT-TTFB"]
        print(f"ChatGPT TTFB: {chat_gpt_ttb}ms, PlayHT TTFB: {play_ht_ttfb}ms")
        headers["X-PlayHT-TTFB"] = str(play_ht_ttfb)
      yield chunk

  return StreamingResponse(audio_generator(),
                           media_type="audio/mpeg",
                           headers=headers)