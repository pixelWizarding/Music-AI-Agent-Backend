from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum

class Call(BaseModel):
    call_sid: Optional[str] = None
    company_id: str
    contact_person_name: str
    contact_person_name_kana: Optional[str] = None
    status: Optional[str] = None
    audio_url: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None


class Event(BaseModel):
    id: str
    event_name: str
    is_success: bool = False
    agent_id: str
    company_ids: List[str]
    events: Optional[List[Call]] = None
    started_at: datetime
    ended_at: datetime
    prompt: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("ended_at")
    def check_ended_after_started(cls, v, values):
        if "started_at" in values and v < values["started_at"]:
            raise ValueError("ended_at must be after started_at")
        return v
