from pydantic import BaseModel
from typing import Optional


class Contact(BaseModel):
    id: Optional[str] = None
    name: str
    staff_name: str
    staff_name_kana: str
    phone_number: str
    hp_url: str
