import httpx
import os
from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import Response

from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import VoiceResponse, Gather
from urllib.parse import quote_plus
from app.services.stream_gpt_text import stream_gpt_text, stream_initial_gpt_response
from app.db.firestore import get_firestore_db
from app.schemas.events import Event
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict
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

@router.get("/trigger_calls")
async def trigger_scheduled_calls():
  db = get_firestore_db()
  current_time = datetime.utcnow() + timedelta(hours=9)
  event_docs = db.collection("events").where('is_success', '==', False).where('started_at', '<', current_time).stream()
  events = [doc.to_dict() for doc in event_docs]

  for event in events:
      for company_id in event['company_ids']:
          contact_docs = db.collection("contacts").where("id", "==", company_id).stream()

          contact_data = None
          for doc in contact_docs:
              contact_data = doc.to_dict()
          
          if contact_data:
              to_phone_number = contact_data['phone_number']
              prompt = event['prompt']
              await call_prompt(to_phone_number=to_phone_number, voice=event['agent_id'], company=company_id, purpose=prompt, requester='Jin')

          event_update_query = db.collection("events").where('id', '==', event['id']).stream()
          event_update_docs = [doc for doc in event_update_query]

          if event_update_docs:
              event_ref = event_update_docs[0].reference
              event_ref.update({'is_success': True, 'updated_at': datetime.utcnow()})

  return {"status": "Calls triggered for events"}
    

@router.get("/say-prompt")
async def say_prompt(voice: str, company: str, purpose: str, requester: str, prompt: Optional[str] = None):
  headers = {}
  if not prompt:
      gpt_stream = stream_initial_gpt_response(requester, company, purpose, lambda ttfb: headers.update({"X-ChatGPT-TTFB": str(ttfb)}))
  else:
      gpt_stream = stream_gpt_text(prompt, requester, company, purpose, lambda ttfb: headers.update({"X-ChatGPT-TTFB": str(ttfb)}))
  
  if gpt_stream is None:
            raise ValueError("GPT stream generation failed, no response from OpenAI API.")
  ssml_text = f"<speak>{''.join([chunk for chunk in gpt_stream])}</speak>"

  audio_url = await generate_audio(ssml_text, voice)

  return {"audio_url": audio_url}

async def generate_audio(ssml_text: str, voice: str) -> str:
  payload = {
      "method": "file",
      "narrationStyle": "Standard",
      "platform": "landing_demo",
      "ssml": ssml_text,
      "userId": PLAY_HT_USER_ID,
      "voice": voice
  }

  async with httpx.AsyncClient(timeout=30.0) as httpx_client:
    response = await httpx_client.post(PLAYHT_API_URL, json=payload, headers=API_HEADERS)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to synthesize audio")

    audio_url = response.json().get("file")
    if not audio_url:
        raise HTTPException(status_code=500, detail="Audio URL not found")

  return audio_url  



call_data = defaultdict(lambda: {"count": 0, "receiver_speech": []})
@router.post("/call-prompt")
async def call_prompt(to_phone_number: str, voice: str, company: str, purpose: str, requester: str):
  call = twilio_client.calls.create(
      to=to_phone_number,
      from_=TWILIO_PHONE_NUMBER,
      url=f"https://aef0-78-46-38-10.ngrok-free.app/calls/twilio-stream?voice={quote_plus(voice)}&company={quote_plus(company)}&purpose={quote_plus(purpose)}&requester={quote_plus(requester)}",
      status_callback=f"https://aef0-78-46-38-10.ngrok-free.app/calls/twilio-status",
      status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
      record=True,
      recording_status_callback=f"https://aef0-78-46-38-10.ngrok-free.app/calls/recording-status",
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

@router.post("/twilio-stream")
async def twilio_stream(voice: str, company: str, purpose: str, requester: str, call_sid: Optional[str] = None):
    response = VoiceResponse()

    if call_sid:
        count = call_data[call_sid]["count"]
        if count < len(call_data[call_sid]["receiver_speech"]):
            current_prompt = call_data[call_sid]["receiver_speech"][count]
        else:
            current_prompt = ""
    else:
        current_prompt = ""
    
    encoded_prompt = quote_plus(current_prompt)

    async with httpx.AsyncClient(timeout=30.0) as httpx_client:
        res_url = f"https://aef0-78-46-38-10.ngrok-free.app/calls/say-prompt?voice={quote_plus(voice)}&company={quote_plus(company)}&purpose={quote_plus(purpose)}&requester={quote_plus(requester)}&prompt={encoded_prompt}"
        res = await httpx_client.get(res_url)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail="Failed to synthesize audio")
        audio_url = res.json().get("audio_url")
        response.play(audio_url)
        gather = Gather(
            input="speech", 
            action=f"/calls/gather-complete?voice={quote_plus(voice)}&company={quote_plus(company)}&purpose={quote_plus(purpose)}&requester={quote_plus(requester)}", 
            method="POST", 
            timeout=5, # Please optimize this timeout.
            language="ja-JP"
        )
        response.append(gather)

    return Response(content=str(response), media_type="application/xml")


@router.post("/gather-complete")
async def gather_complete(voice: str, company: str, purpose: str, requester: str, request: Request):
    form_data = await request.form()
    speech_result = form_data.get("SpeechResult")
    call_sid = form_data.get("CallSid")
    print(f"Receiver said in Japanese: {speech_result}")
    call_data[call_sid]["receiver_speech"].append(speech_result)
    call_data[call_sid]["count"] += 1
    response = VoiceResponse()
    response.redirect(f"/calls/twilio-stream?voice={quote_plus(voice)}&company={quote_plus(company)}&purpose={quote_plus(purpose)}&requester={quote_plus(requester)}&call_sid={call_sid}")
    
    return Response(content=str(response), media_type="application/xml")