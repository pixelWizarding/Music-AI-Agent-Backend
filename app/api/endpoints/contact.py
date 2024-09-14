from fastapi import APIRouter, HTTPException
from app.schemas.contact import ContactCreate, ContactResponse
from app.db.firestore import get_firestore_db
from app.db.redis import get_redis_client

router = APIRouter()

@router.post("/add-contact/")
async def add_contact(contact: ContactCreate):
    db = get_firestore_db()
    
    docs = db.collection("contacts").where("company_id", "==", contact.company_id).stream()
    if list(docs):
        raise HTTPException(status_code=400, detail="Company ID already exists")
    
    db.collection("contacts").add(contact.dict())
    return {"message": "Contact added successfully!"}

@router.get("/get-contacts/")
async def get_all_contacts():
    db = get_firestore_db()
    
    docs = db.collection("contacts").stream()

    contacts = [doc.to_dict() for doc in docs]

    return contacts

@router.get("/get-contact/{company_id}")
async def get_contact(company_id: int):
    db = get_firestore_db()
    
    docs = db.collection("contacts").where("company_id", "==", company_id).stream()
    
    contact_data = None
    for doc in docs:
        contact_data = doc.to_dict()

    if not contact_data:
        raise HTTPException(status_code=404, detail="Contact not found")

    return contact_data

