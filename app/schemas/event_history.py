from pydantic import BaseModel, Field
from datetime import datetime


class EventHistory(BaseModel):
    company_id: str
    call_id: str
    status: str
    audio_url: str
    duration: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
