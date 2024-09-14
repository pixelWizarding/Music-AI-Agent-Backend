from fastapi import APIRouter
from app.api.endpoints import contact

router = APIRouter()
router.include_router(contact.router, prefix="/contacts", tags=["Contacts"])
