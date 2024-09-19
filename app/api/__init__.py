from fastapi import APIRouter
from app.api.endpoints import contact
from app.api.endpoints import events

router = APIRouter()
router.include_router(contact.router, prefix="/contacts", tags=["Contacts"])
router.include_router(events.router, prefix="/events", tags=["Events"])
