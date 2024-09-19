from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum


class EventStatus(str, Enum):
    success = "Success"
    failure = "Failure"
    pending = "Pending"


class Event(BaseModel):
    id: str
    contact_person_name: str
    contact_person_name_kana: Optional[str] = None
    status: EventStatus
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


class EventSession(BaseModel):
    id: str
    event_name: str
    is_success: bool
    agent_id: str
    company_id: str
    events: List[Event]  # Multiple events
    feedback: Optional[Feedback] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
