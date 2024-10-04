from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime, timezone
from app.schemas.events import Event
from app.db.firestore import get_firestore_db

router = APIRouter()


@router.post("/add-event/")
async def add_event(event: Event):
    db = get_firestore_db()

    docs = db.collection("events").where("id", "==", event.id).stream()
    if list(docs):
        raise HTTPException(status_code=400, detail="Company ID already exists")

    event_data = event.dict()
    db.collection("events").add(event_data)
    return {"message": "Events added successfully!"}


@router.get("/get-events/")
async def get_all_events():
    db = get_firestore_db()

    event_docs = db.collection("events").stream()
    events = [doc.to_dict() for doc in event_docs]

    return events


@router.get("/get-events/{id}")
async def get_event(id: str):
    db = get_firestore_db()

    # Fetch the event
    event_docs = db.collection("events").where("id", "==", id).stream()
    event_data = None
    for doc in event_docs:
        event_data = doc.to_dict()

    if not event_data:
        raise HTTPException(status_code=404, detail="Event not found")

    return event_data


@router.put("/update-event/{id}")
async def update_event(id: str, event: Event):
    db = get_firestore_db()

    query = db.collection("events").where("id", "==", id).limit(1)
    results = query.get()

    if not results:
        raise HTTPException(status_code=404, detail="Event not found")

    doc_ref = results[0].reference
    doc_ref.update(event.dict())

    return {"message": "Event updated successfully!"}


@router.delete("/delete-event/{id}")
async def delete_event(id: str):
    db = get_firestore_db()

    query = db.collection("events").where("id", "==", id).limit(1)
    results = query.get()

    if not results:
        raise HTTPException(status_code=404, detail="Event not found")

    doc_ref = results[0].reference
    doc_ref.delete()

    return {"message": "Event deleted successfully!"}


@router.post("/trigger-scheduled-calls")
async def trigger_scheduled_calls(background_tasks: BackgroundTasks):
    db = get_firestore_db()
    now = datetime.now(timezone.utc)
    events = db.collection('events').where('started_at', '<=', now).where('is_success', '==', False).stream()

    events_triggered = 0
    for event in events:
        event_data = event.to_dict()
        event_id = event.id

        try:
            background_tasks.add_task(update_calls_data, event_data['recipient_phone_number'], event_data['agent_id'])

            print(f"Triggering call for event {event_id}")
            event.reference.update({
                "is_success": True,
                "updated_at": datetime.utcnow()
            })
            events_triggered += 1
        except Exception as e:
            print(f"Failed to trigger call for event {event_id}: {e}")

    if events_triggered == 0:
        return {"message": "No events triggered at this time."}

    return {"message": f"{events_triggered} events triggered successfully."}

import uuid

async def append_calls_data(recipient_phone_number: str, agent_id: str):
    db = firestore.Client()
    # Fetch the events that have not been marked as successful
    events_ref = db.collection('events').where('agent_id', '==', agent_id).stream()

    for event in events_ref:
        event_data = event.to_dict()
        event_id = event.id
        company_ids = event_data.get('company_ids', [])

        call_results = []
        for company_id in company_ids:
            # Create a test call result for each company_id
            call_result = {
                "id": str(uuid.uuid4()),  # Generating a unique value for the call ID
                "company_id": company_id,
                "contact_person_name": "Jin",
                "contact_person_name_kana": "Jin",  # Optional field, could be filled or left as None
                "status": "Success",
                "audio_url": "http://commondatastorage.googleapis.com/codeskulptor-assets/week7-brrring.m4a",
                "started_at": datetime.utcnow(),
                "ended_at": datetime.utcnow(),
            }
            call_results.append(call_result)

        # Append the call results to the event's existing 'events' field
        try:
            event.reference.update({
                "events": firestore.ArrayUnion(call_results),
                "is_success": True,  # Marking the event as successfully triggered
                "updated_at": datetime.utcnow()
            })
            print(f"Call results appended for event {event_id}")
        except Exception as e:
            print(f"Failed to update event {event_id}: {e}")
