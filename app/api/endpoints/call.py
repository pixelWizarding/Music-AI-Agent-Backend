import httpx
import os
from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import Response

from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import VoiceResponse, Gather
from urllib.parse import quote_plus
from app.services.stream_gpt_text import stream_gpt_text, stream_initial_gpt_response, analyze_response
from app.db.firestore import get_firestore_db
from app.schemas.events import Event, Call
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict
import random
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

def get_current_time():
    return datetime.utcnow() + timedelta(hours=9)

@router.get("/trigger_calls")
async def trigger_scheduled_calls():
    db = get_firestore_db()
    current_time = get_current_time()
    event_docs = db.collection("events").where('is_success', '==', False).where('started_at', '<', current_time).stream()
    events = [doc.to_dict() for doc in event_docs]

    for event in events:
        call_records = []
        event_id = event['id']
        for company_id in event['company_ids']:
            contact_docs = db.collection("contacts").where("id", "==", company_id).stream()

            contact_data = None
            for doc in contact_docs:
                contact_data = doc.to_dict()
            
            if contact_data:
                to_phone_number = contact_data['phone_number']
                prompt = event['prompt']
                requester='Jin'
                try:
                    call_result = await call_prompt(to_phone_number=to_phone_number, voice=event['agent_id'], company=company_id, purpose=prompt, requester=requester, event_id = event_id )
                    call_record = Call(
                        call_sid=call_result['call_sid'],
                        company_id=company_id,
                        contact_person_name=requester,
                        started_at=current_time,
                        status='4'
                    )
                
                except Exception as e:
                    print(f"Error occurred while calling {to_phone_number} for company {company_id}: {str(e)}")
                    call_record = Call(
                        company_id=company_id,
                        contact_person_name=requester,
                        status='0',
                        started_at=current_time                    
                    )
                    continue
                
                call_records.append(call_record.dict())

        event_update_query = db.collection("events").where('id', '==', event_id).stream()
        event_update_docs = [doc for doc in event_update_query]

        if event_update_docs:
            event_ref = event_update_docs[0].reference
            event_ref.update({'events': call_records, 'is_success': True, 'updated_at': datetime.utcnow()})

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
async def call_prompt(to_phone_number: str, voice: str, company: str, purpose: str, requester: str, event_id: str):
    try:
        call = twilio_client.calls.create(
            to=to_phone_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"https://d7e0-35-200-63-31.ngrok-free.app/calls/twilio-stream?voice={quote_plus(voice)}&company={quote_plus(company)}&purpose={quote_plus(purpose)}&requester={quote_plus(requester)}",
            record=True,
            recording_status_callback=f"https://d7e0-35-200-63-31.ngrok-free.app/calls/recording-status?event_id={event_id}",
        )
        return {"status": "Call initiated", "call_sid": call.sid}
    except Exception as e:
        print(f"Error occurred while initiating call: {str(e)}")
        return {"status": "Call failed", "error": str(e)}


@router.post("/recording-status")
async def recording_status(event_id: str, request: Request):
    form_data = await request.form()
    
    call_sid = form_data.get("CallSid")
    recording_url = form_data.get("RecordingUrl") + ".mp3"

    if call_data[call_sid] and call_data[call_sid]["receiver_speech"]:
        call_result = " ".join(call_data[call_sid]["receiver_speech"])
        call_status = analyze_response(call_result)

    else:
        call_status = '4'

    db = get_firestore_db()

    event_docs = db.collection("events").where('id', '==', event_id).stream()
    event_docs = [doc for doc in event_docs]

    if not event_docs:
        return {"status": "Event not found", "event_id": event_id}, 404

    event_ref = event_docs[0].reference
    event_data = event_docs[0].to_dict()

    updated_calls = []
    call_found = False
    current_time = get_current_time()

    if 'events' in event_data:
        for call in event_data['events']:
            if call.get('call_sid') == call_sid:
                call['audio_url'] = recording_url
                call['status'] = call_status
                call['ended_at'] = current_time
                call_found = True
            updated_calls.append(call)

    if not call_found:
        return {"status": "Call record not found", "call_sid": call_sid}, 404

    try:
        event_ref.update({
            'events': updated_calls,
            'updated_at': current_time
        })
    except Exception as e:
        print(f"Error save call record: {str(e)}")

    print(f"Recording available for call {call_sid}: {recording_url}")

    return {"status": "Recording received and updated", "recording_url": recording_url}

PREFIX_SPEECHES = ["はい", "えと", "なるほど", "そうなんですね", "もしもし"]
@router.post("/twilio-stream")
async def twilio_stream(voice: str, company: str, purpose: str, requester: str, call_sid: Optional[str] = None):
    response = VoiceResponse()

    if call_sid:
        count = call_data[call_sid]["count"]
        if count <= len(call_data[call_sid]["receiver_speech"]):
            current_prompt = call_data[call_sid]["receiver_speech"][count-1]
        else:
            current_prompt = ""
    else:
        current_prompt = ""
    
    encoded_prompt = quote_plus(current_prompt)

    async with httpx.AsyncClient(timeout=30.0) as httpx_client:
        res_url = f"https://d7e0-35-200-63-31.ngrok-free.app/calls/say-prompt?voice={quote_plus(voice)}&company={quote_plus(company)}&purpose={quote_plus(purpose)}&requester={quote_plus(requester)}&prompt={encoded_prompt}"
        res = await httpx_client.get(res_url)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail="Failed to synthesize audio")
        audio_url = res.json().get("audio_url")
        response.play(audio_url)
        gather = Gather(
            input="speech", 
            action=f"/calls/gather-complete?voice={quote_plus(voice)}&company={quote_plus(company)}&purpose={quote_plus(purpose)}&requester={quote_plus(requester)}", 
            method="POST", 
            timeout=15,
            speech_timeout=2,
            language="ja-JP"
        )
        response.append(gather)

    return Response(content=str(response), media_type="application/xml")


@router.post("/gather-complete")
async def gather_complete(voice: str, company: str, purpose: str, requester: str, request: Request):
    form_data = await request.form()
    speech_result = form_data.get("SpeechResult")
    call_sid = form_data.get("CallSid")

    if speech_result:
        print(f"Receiver said in Japanese: {speech_result}")
        call_data[call_sid]["receiver_speech"].append(speech_result)
        call_data[call_sid]["count"] += 1
    else:
        print("No speech detected, continuing the call")

    response = VoiceResponse()
    prefix_speech = random.choice(PREFIX_SPEECHES)
    prefix_ssml = f"<speak>{prefix_speech}</speak>"
    prefix_audio_url = await generate_audio(prefix_ssml, voice)
    response.play(prefix_audio_url)

    response.redirect(f"/calls/twilio-stream?voice={quote_plus(voice)}&company={quote_plus(company)}&purpose={quote_plus(purpose)}&requester={quote_plus(requester)}&call_sid={call_sid}")
    
    return Response(content=str(response), media_type="application/xml")