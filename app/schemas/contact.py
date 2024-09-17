from pydantic import BaseModel


class Contact(BaseModel):
    id: str
    name: str
    staff_name: str
    staff_name_kana: str
    phone_number: str
    hp_url: str
