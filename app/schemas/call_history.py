from pydantic import BaseModel, Field
from datetime import datetime


class CallHistory(BaseModel):
    company_id: str  # Reference to Companies collection
    call_id: str  # Reference to Events collection
    status: str
    audio_url: str
    duration: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "company_id": "company_123",
                "call_id": "call_123",
                "status": "Completed",
                "audio_url": "https://example.com/call_123.mp3",
                "duration": 1800,
                "created_at": "2024-01-01T12:00:00Z",
            }
        }
