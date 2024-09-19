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

    contacts = [doc.to_dict() for doc in docs]

    return contacts
