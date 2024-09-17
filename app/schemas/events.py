from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum


class CallStatus(str, Enum):
    success = "Success"
    failure = "Failure"
    pending = "Pending"


class Call(BaseModel):
    id: str
    contact_person_name: str
    contact_person_name_kana: Optional[str] = None
    status: CallStatus
    audio_url: str
    started_at: datetime
    ended_at: datetime

    @validator("ended_at")
    def check_ended_after_started(cls, v, values):
        if "started_at" in values and v < values["started_at"]:
            raise ValueError("ended_at must be after started_at")
        return v


class Feedback(BaseModel):
    sentiment_analysis: str
    feedback_score: float
    updated_tone: str


class CallSession(BaseModel):
    id: str
    event_name: str
    is_success: bool
    agent_id: str
    company_id: str
    calls: List[Call]  # Multiple calls
    feedback: Optional[Feedback] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "id": "event_123",
                "event_name": "Call to Client A",
                "is_success": True,
                "agent_id": "agent_123",
                "company_id": "company_123",
                "calls": [
                    {
                        "id": "call_123",
                        "contact_person_name": "John Doe",
                        "contact_person_name_kana": "ジョン ドゥ",
                        "status": "Success",
                        "audio_url": "https://example.com/call_123.mp3",
                        "started_at": "2024-01-01T12:00:00Z",
                        "ended_at": "2024-01-01T12:30:00Z",
                    }
                ],
                "feedback": {
                    "sentiment_analysis": "Positive",
                    "feedback_score": 8.5,
                    "updated_tone": "Cheerful",
                },
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-02T12:00:00Z",
            }
        }
