# app/modules/domains/schema.py
from pydantic import BaseModel
from datetime import datetime

class DomainBase(BaseModel):
    name: str

class DomainCreate(DomainBase):
    pass

class DomainUpdate(DomainBase):
    pass

class DomainOut(DomainBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
