from pydantic import BaseModel
from datetime import datetime

class EventRegistrationCreate(BaseModel):
    user_id: int

class EventRegistrationOut(BaseModel):
    id: int
    event_id: int
    user_id: int
    registered_at: datetime
    status: str

    class Config:
        from_attributes = True  # Pydantic v2 replacement for orm_mode
