from pydantic import BaseModel, Field
from typing import Optional


class Contact(BaseModel):
    id: Optional[str] = Field(default=None)
    name: str
    staff_name: str
    staff_name_kana: str
    phone_number: str
    hp_url: str
