from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ExternalData(BaseModel):
    data: Optional[str] = None


class Agent(BaseModel):
    id: str
    name: str
    personality: str
    voice: str
    tone: str
    external_data: Optional[ExternalData] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def update(self, **kwargs):
        # Update fields with provided values
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Update the updated_at timestamp
        self.updated_at = datetime.utcnow()

    class Config:
        schema_extra = {
            "example": {
                "id": "agent_123",
                "name": "Agent A",
                "personality": "Cheerful",
                "voice": "PlayHT Voice Model 1",
                "tone": "Polite",
                "external_data": {"data": "Metadata about the agent"},
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-02T12:00:00Z",
            }
        }
