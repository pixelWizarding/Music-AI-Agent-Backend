from pydantic import BaseModel, HttpUrl

class ContactCreate(BaseModel):
    company_id: int
    company_name: str
    phone_number: str
    HP_url: str 

class ContactResponse(BaseModel):
    company_id: int
    company_name: str
    phone_number: str
    HP_url: str
