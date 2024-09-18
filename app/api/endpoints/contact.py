from fastapi import APIRouter, HTTPException
from app.schemas.contact import Contact
from app.db.firestore import get_firestore_db

router = APIRouter()


@router.post("/add-contact/")
async def add_contact(contact: Contact):
    db = get_firestore_db()

    docs = db.collection("contacts").where("id", "==", contact.id).stream()
    if list(docs):
        raise HTTPException(status_code=400, detail="Company ID already exists")

    contact_data = contact.dict()
    db.collection("contacts").add(contact_data)
    return {"message": "Contact added successfully!"}


@router.get("/get-contacts/")
async def get_all_contacts():
    db = get_firestore_db()

    docs = db.collection("contacts").stream()

    contacts = [doc.to_dict() for doc in docs]

    return contacts


@router.get("/get-contact/{id}")
async def get_contact(id: str):
    db = get_firestore_db()

    docs = db.collection("contacts").where("id", "==", id).stream()

    contact_data = None
    for doc in docs:
        contact_data = doc.to_dict()

    if not contact_data:
        raise HTTPException(status_code=404, detail="Contact not found")

    return contact_data


@router.put("/update-contact/{id}")
async def update_contact(id: str, contact: Contact):
    db = get_firestore_db()

    query = db.collection("contacts").where("id", "==", id).limit(1)
    results = query.get()

    if not results:
        raise HTTPException(status_code=404, detail="Contact not found")

    doc_ref = results[0].reference
    doc_ref.update(contact.dict())

    return {"message": "Contact updated successfully!"}


@router.delete("/delete-contact/{id}")
async def delete_contact(id: str):
    db = get_firestore_db()

    query = db.collection("contacts").where("id", "==", id).limit(1)
    results = query.get()

    if not results:
        raise HTTPException(status_code=404, detail="Contact not found")

    doc_ref = results[0].reference
    doc_ref.delete()

    return {"message": "Contact deleted successfully!"}
