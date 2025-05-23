import httpx
import os
import time
from pyht import Client
from pyht.client import TTSOptions, Format, Language
from fastapi import HTTPException, APIRouter, Request
from fastapi.responses import Response, StreamingResponse

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

if os.getenv("PLAY_HT_USER_ID") and os.getenv("PLAY_HT_API_KEY"):
  pht_client = Client(
      user_id=os.getenv("PLAY_HT_USER_ID"),
      api_key=os.getenv("PLAY_HT_API_KEY"),
  )
else:
  pht_client = None

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
async def say_prompt(voice: str, company: str, purpose: str, requester: str, call_sid: Optional[str] = None):
    print('call_sid --->', type(call_sid))
    if call_sid:
        count = call_data[call_sid]["count"]
        if count <= len(call_data[call_sid]["receiver_speech"]):
            current_prompt = call_data[call_sid]["receiver_speech"][count-1]
        else:
            current_prompt = ""

        # Collect last responses from 0 to count - 2
        if count > 1:
            last_responses = call_data[call_sid]["receiver_speech"][:count-1]
        else:
            last_responses = []
    else:
        current_prompt = ""
    
    headers = {}
    options = TTSOptions(
        voice="s3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json",
        language=Language.JAPANESE,
        sample_rate=44100,
        speed=0.85,
        format=Format.FORMAT_MP3
    )
    

    if not current_prompt:
        gpt_stream = stream_initial_gpt_response(requester, company, purpose, lambda ttfb: headers.update({"X-ChatGPT-TTFB": str(ttfb)}))
    else:
        gpt_stream = stream_gpt_text(current_prompt, requester, company, purpose, lambda ttfb: headers.update({"X-ChatGPT-TTFB": str(ttfb)}), last_responses=last_responses)

    if gpt_stream is None:
        raise ValueError("GPT stream generation failed, no response from OpenAI API.")

    gpt_full_response = ''.join([chunk for chunk in gpt_stream])

    # Now that we have the complete response, send it to PlayHT
    def audio_generator():
        is_first_chunk = True
        start_time = int(time.time() * 2000)

        for chunk in pht_client.tts(gpt_full_response, options):
            if is_first_chunk:
                is_first_chunk = False
                end_time = int(time.time() * 2000)
                play_ht_ttfb = end_time - start_time

                chat_gpt_ttb = headers["X-ChatGPT-TTFB"]
                print(f"ChatGPT TTFB: {chat_gpt_ttb}ms, PlayHT TTFB: {play_ht_ttfb}ms")
                headers["X-PlayHT-TTFB"] = str(play_ht_ttfb)
            yield chunk

    return StreamingResponse(audio_generator(), media_type="audio/mpeg", headers=headers)


call_data = defaultdict(lambda: {"count": 0, "receiver_speech": []})
async def call_prompt(to_phone_number: str, voice: str, company: str, purpose: str, requester: str, event_id: str):
    try:
        call = twilio_client.calls.create(
            to=to_phone_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"https://fc71-78-46-38-10.ngrok-free.app/calls/twilio-stream?voice={quote_plus(voice)}&company={quote_plus(company)}&purpose={quote_plus(purpose)}&requester={quote_plus(requester)}",
            record=True,
            recording_status_callback=f"https://fc71-78-46-38-10.ngrok-free.app/calls/recording-status?event_id={event_id}",
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

PREFIX_SPEECHES = [
    "はい、ありがとうございます。",
    "えと、いつもありがとうございます。",
    "なるほど、感謝いたします。",
    "そうなんですね、ありがとうございます。",
    "はい、ご連絡ありがとうございます。",
    "ええ、すみません、ありがとうございます。",
    "はい、どうもありがとうございます。",
    "そうですね、ありがとうございます。"
]
@router.post("/twilio-stream")
async def twilio_stream(voice: str, company: str, purpose: str, requester: str, call_sid: Optional[str] = None):
    response = VoiceResponse()
    print("--->", call_sid)
    if call_sid:
        res_url = f"https://fc71-78-46-38-10.ngrok-free.app/calls/say-prompt?voice={quote_plus(voice)}&company={quote_plus(company)}&purpose={quote_plus(purpose)}&requester={quote_plus(requester)}&call_sid={call_sid}"
    else:
        res_url = f"https://fc71-78-46-38-10.ngrok-free.app/calls/say-prompt?voice={quote_plus(voice)}&company={quote_plus(company)}&purpose={quote_plus(purpose)}&requester={quote_plus(requester)}"

    response.play(res_url)
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
    response.redirect(f"/calls/twilio-stream?voice={quote_plus(voice)}&company={quote_plus(company)}&purpose={quote_plus(purpose)}&requester={quote_plus(requester)}&call_sid={call_sid}")
    
    return Response(content=str(response), media_type="application/xml")