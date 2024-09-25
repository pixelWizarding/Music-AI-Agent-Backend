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

    event_docs = db.collection("events").stream()
    events = []

    for event_doc in event_docs:
        event_data = event_doc.to_dict()

        agent_docs = (
            db.collection("agents").where("id", "==", event_data["agent_id"]).stream()
        )
        agent_data = None

        for agent_doc in agent_docs:
            agent_data = agent_doc.to_dict()

        if event_data.get("events"):
            for call in event_data["events"]:
                company_docs = (
                    db.collection("contacts")
                    .where("id", "==", call["company_id"])
                    .stream()
                )
                company_data = None

                for company_doc in company_docs:
                    company_data = company_doc.to_dict()
                call["company_name"] = company_data["name"] if company_data else None
        event_response = {
            **event_data,
            "agent_name": agent_data["name"] if agent_data else None,
            "events": event_data["events"],
        }
        events.append(event_response)

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

    # Fetch agent details using agent_id
    agent_docs = (
        db.collection("agents").where("id", "==", event_data["agent_id"]).stream()
    )
    agent_data = None

    for agent_doc in agent_docs:
        agent_data = agent_doc.to_dict()

    if event_data.get("events"):
        for call in event_data["events"]:
            company_docs = (
                db.collection("contacts").where("id", "==", call["company_id"]).stream()
            )
            company_data = None

            for company_doc in company_docs:
                company_data = company_doc.to_dict()
            call["company_name"] = company_data["name"] if company_data else None
    event_response = {
        **event_data,
        "agent_name": agent_data["name"] if agent_data else None,
        "events": event_data["events"],
    }

    return event_response


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
