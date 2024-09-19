from fastapi import APIRouter, HTTPException
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

    docs = db.collection("events").stream()

    events = [doc.to_dict() for doc in docs]

    return events


@router.get("/get-events/{id}")
async def get_event(id: str):
    db = get_firestore_db()

    docs = db.collection("events").where("id", "==", id).stream()

    event_data = None
    for doc in docs:
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
