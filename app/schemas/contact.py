from pydantic import BaseModel


class Contact(BaseModel):
    id: str  # Firestore stores ids as strings, even for bigints
    name: str
    staff_name: str
    staff_name_kana: str
    phone_number: str
    # Firestore does not enforce unique indexes, but you can handle this on app logic
    hp_url: str  # Same as phone_number

    class Config:
        schema_extra = {
            "example": {
                "id": "1234567890123456789",
                "name": "John Doe",
                "staff_name": "Jane Smith",
                "staff_name_kana": "ジェーン スミス",
                "phone_number": "+1234567890",
                "hp_url": "https://example.com",
            }
        }
