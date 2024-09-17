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
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.updated_at = datetime.utcnow()
