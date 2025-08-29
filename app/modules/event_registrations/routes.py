from fastapi import APIRouter, Depends
from modules.event_registrations import service, schema
from db.connection import get_db

router = APIRouter()

@router.post("/{event_id}/register", response_model=schema.EventRegistrationOut)
def register_user(event_id: int, registration: schema.EventRegistrationCreate, db=Depends(get_db)):
    return service.register_user(event_id, registration.user_id, db=db)

@router.get("/{event_id}/registrations", response_model=list[schema.EventRegistrationOut])
def list_registrations(event_id: int, db=Depends(get_db)):
    return service.list_registrations(event_id, db=db)
