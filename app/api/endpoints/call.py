import httpx
import os
from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import Response

from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import VoiceResponse
from urllib.parse import quote_plus
from app.services.stream_gpt_text import stream_gpt_text
from dotenv import load_dotenv
load_dotenv()

router = APIRouter()
PLAY_HT_USER_ID = os.getenv('PLAY_HT_USER_ID')
PLAY_HT_API_KEY = os.getenv('PLAY_HT_API_KEY')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
PLAYHT_API_URL = "https://play.ht/api/transcribe"
API_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {PLAY_HT_API_KEY}"  # Replace with your PlayHT API key
}

@router.get("/say-prompt")
async def say_prompt(prompt: str):
  headers = {}
  gpt_stream = stream_gpt_text(prompt, lambda ttfb: headers.update({"X-ChatGPT-TTFB": str(ttfb)}))
  ssml_text = "<speak><p>"
  for chunk in gpt_stream:
      ssml_text += chunk
  ssml_text += "</p></speak>"
  payload = {
      "method": "file",
      "narrationStyle": "Neural",
      "platform": "landing_demo",
      "ssml": ssml_text,
      "userId": PLAY_HT_USER_ID,
      "voice": "ja-JP-Wavenet-C"
  }
  async with httpx.AsyncClient(timeout=30.0) as httpx_client:
      response = await httpx_client.post(PLAYHT_API_URL, json=payload, headers=API_HEADERS)

      if response.status_code != 200:
          raise HTTPException(status_code=response.status_code, detail="Failed to synthesize audio")

      audio_url = response.json().get("file")

      if not audio_url:
          raise HTTPException(status_code=500, detail="Audio URL not found")

  return {"audio_url": audio_url}
  



prompts_queue = []

@router.post("/call-prompt")
async def call_prompt(prompt: str, to_phone_number: str):
  prompts_queue.append(prompt)

  call = twilio_client.calls.create(
      to=to_phone_number,
      from_=TWILIO_PHONE_NUMBER,
      url=f"https://6e29-78-46-38-10.ngrok-free.app/calls/twilio-stream",
      status_callback=f"https://6e29-78-46-38-10.ngrok-free.app/calls/twilio-status",
      status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
      record=True,
      recording_status_callback=f"https://6e29-78-46-38-10.ngrok-free.app/calls/recording-status",
  )
  return {"status": "Call initiated", "call_sid": call.sid}

@router.post("/twilio-status")
async def twilio_status(request: Request):
    form_data = await request.form()

    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")

    print(f"Call SID: {call_sid}, Status: {call_status}")

    if call_status == "completed":
        print(f"Call {call_sid} completed")
    
    return {"status": "Callback received"}

@router.post("/recording-status")
async def recording_status(request: Request):
    form_data = await request.form()

    # Get the recording details
    call_sid = form_data.get("CallSid")
    recording_sid = form_data.get("RecordingSid")
    recording_url = form_data.get("RecordingUrl") + ".mp3"

    print(f"Recording available for call {call_sid}: {recording_url}")

    return {"status": "Recording received", "recording_url": recording_url}

@router.post("/transcription-status")
async def transcription_status(request: Request):
    form_data = await request.form()

    # Get the transcription details
    transcription_sid = form_data.get("TranscriptionSid")
    transcription_text = form_data.get("TranscriptionText")
    call_sid = form_data.get("CallSid")

    # Log or save the transcription
    print(f"Transcription for call {call_sid}: {transcription_text}")

    return {"status": "Transcription received", "transcription_text": transcription_text}

@router.post("/twilio-stream")
async def twilio_stream():
    response = VoiceResponse()

    if prompts_queue:
        current_prompt = prompts_queue.pop(0)
        encoded_prompt = quote_plus(current_prompt)
        
        async with httpx.AsyncClient(timeout=30.0) as httpx_client:
          res_url = f"https://6e29-78-46-38-10.ngrok-free.app/calls/say-prompt?prompt={encoded_prompt}"
          res = await httpx_client.get(res_url)
          if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail="Failed to synthesize audio")
          audio_url = res.json().get("audio_url")

          response.play(audio_url)
          response.redirect(f"https://6e29-78-46-38-10.ngrok-free.app/calls/twilio-stream")
    else:
        response.pause(length=3)
        response.redirect(f"https://6e29-78-46-38-10.ngrok-free.app/calls/twilio-stream")
    
    return Response(content=str(response), media_type="application/xml")

@router.post("/add-prompt")
async def add_prompt(prompt: str):
    prompts_queue.append(prompt)
    return {"status": "Prompt added", "prompt": prompt}