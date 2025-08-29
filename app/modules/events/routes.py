from fastapi import APIRouter, Depends, HTTPException
from modules.events import service, schema
from db.connection import get_db

router = APIRouter()

@router.get("/", response_model=list[schema.EventOut])
def get_events(domain_id: int = None, event_type: str = None, db=Depends(get_db)):
    return service.list_events(db=db, domain_id=domain_id, event_type=event_type)

@router.get("/{event_id}", response_model=schema.EventOut)
def get_event(event_id: int, db=Depends(get_db)):
    event = service.get_event(event_id, db=db)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.post("/", response_model=schema.EventOut)
def create_event(event_data: schema.EventCreate, db=Depends(get_db)):
    return service.create_event(event_data, db=db)

@router.put("/{event_id}", response_model=schema.EventOut)
def update_event(event_id: int, event_data: schema.EventUpdate, db=Depends(get_db)):
    updated = service.update_event(event_id, event_data, db=db)
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    return updated

@router.delete("/{event_id}", response_model=schema.EventOut)
def delete_event(event_id: int, db=Depends(get_db)):
    deleted = service.delete_event(event_id, db=db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found")
    return deleted
