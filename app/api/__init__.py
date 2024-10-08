from fastapi import APIRouter
from app.api.endpoints import contact
from app.api.endpoints import events
# from app.api.endpoints import agent
from app.api.endpoints import call

router = APIRouter()
router.include_router(contact.router, prefix="/contacts", tags=["Contacts"])
router.include_router(events.router, prefix="/events", tags=["Events"])
# router.include_router(agent.router, prefix="/agents", tags=["Agents"])
router.include_router(call.router, prefix="/calls", tags=["Calls"])
